import logging

import base64
import hashlib
import json
import os
import re
import secrets
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urljoin, urlparse

import requests
from dataclasses_json import dataclass_json

from .constants import (
    ANDROID_CLIENT_ID,
    APP_VERSION,
    BASE_URL,
    DEFAULT_COUNTRY,
    DEFAULT_LOCALE,
    DEVICE_MODEL,
    DEVICE_OS,
    IDENTITY_URL,
    REDIRECT_URI,
    USER_AGENT_APP,
    USER_AGENT_WEB,
)
from .errors import AuthenticationError, VWClientError, VehicleSessionError
from .models import (
    AccessTokenExchangeRequest,
    AccessTokenResponse,
    EVSummaryResponse,
    GarageResponse,
    RefreshTokenRequest,
    SpinChallengeResponse,
    VehicleLocationResponse,
    VehicleResponse,
    VehicleSessionRequest,
    VehicleSessionResponse,
)
from .models.generic import GenericCorrelationIdResponse

logger = logging.getLogger(__name__)


@dataclass_json
@dataclass
class VWVehicle:
    id: str
    tsp: str
    token: str | None = None
    expires_at: float = 0.0


@dataclass_json
@dataclass
class VWSessionState:
    app_uuid: str = field(default_factory=lambda: str(uuid.uuid4()))
    mobile_session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    locale: str = DEFAULT_LOCALE
    country: str = DEFAULT_COUNTRY
    access_token: str | None = None
    access_token_expires_at: float = 0.0
    id_token: str | None = None
    id_token_expires_at: float = 0.0
    refresh_token: str | None = None
    refresh_token_expires_at: float = 0.0
    user_id: str | None = None
    vehicles: dict[str, VWVehicle] = field(default_factory=dict)
    email: str | None = None


class VWClient:
    def __init__(
        self,
        email: str,
        password: str,
        spin: str,
        *,
        session_path: str | os.PathLike[str] | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.email = email
        self.password = password
        self.spin = spin
        self.session_path = Path(
            session_path or Path.home() / ".vw_client" / "session.json"
        )
        self.timeout = timeout
        self.session = requests.Session()
        self.state = self._load_state()

        if self.state.email and self.state.email != email:
            logger.info("Resetting session state after email change")
            self.state = VWSessionState()
        self.state.email = email

        if not self.state.vehicles:
            self._load_vehicles()

    def login(self, *, force: bool = False) -> None:
        logger.debug("Ensuring authenticated session (force=%s)", force)
        if not force and self._try_refresh_access_token():
            return

        logger.info("Refreshing access token was not possible; performing full login")
        self._perform_full_login()

    def _load_vehicles(self) -> None:
        logger.info("Loading vehicles into session state")

        self.login()

        result: dict[str, VWVehicle] = {}

        garage = self.get_garage()
        for vehicle in garage.data.vehicles:
            logger.debug("Caching vehicle %s", vehicle.vehicleId)
            result[vehicle.vehicleId] = VWVehicle(
                id=vehicle.vehicleId,
                tsp=vehicle.tspProvider,
            )

        self.state.vehicles = result

        self._save_state()

    def get_garage(self) -> GarageResponse:
        logger.debug("Fetching garage")
        response = self._request(
            "GET",
            f"{BASE_URL}/account/v1/garage",
            params={"idToken": self._require(self.state.id_token, "Missing id token")},
            token=self._require(self.state.access_token, "Missing access token"),
            user_id_header="",
        )

        return GarageResponse.model_validate(self._decode_json(response))

    def get_vehicle(self, vehicle_id: str) -> VehicleResponse:
        logger.debug("Fetching vehicle status for %s", vehicle_id)
        response = self._request(
            "GET",
            f"{BASE_URL}/rvs/v1/vehicle/{vehicle_id}",
            token=self._resolve_vehicle_token(vehicle_id),
            user_id_header=self._require(self.state.user_id, "Missing user id"),
        )

        return VehicleResponse.model_validate(self._decode_json(response))

    def get_vehicle_location(self, vehicle_id: str) -> VehicleLocationResponse:
        logger.debug("Fetching vehicle location for %s", vehicle_id)
        response = self._request(
            "GET",
            f"{BASE_URL}/rvs/v1/location/vehicle/{vehicle_id}",
            token=self._resolve_vehicle_token(vehicle_id),
            user_id_header=self._require(self.state.user_id, "Missing user id"),
        )

        return VehicleLocationResponse.model_validate(self._decode_json(response))

    def get_ev_summary(
        self, vehicle_id: str, temp_unit: str = "f"
    ) -> EVSummaryResponse:
        logger.debug("Fetching EV summary for %s", vehicle_id)
        user_id = self._require(self.state.user_id, "Missing user id")
        response = self._request(
            "GET",
            f"{BASE_URL}/ev/v1/user/{user_id}/vehicle/{vehicle_id}/summary",
            params={"tempUnit": temp_unit},
            token=self._resolve_vehicle_token(vehicle_id),
            user_id_header=user_id,
        )

        return EVSummaryResponse.model_validate(self._decode_json(response))

    def start_ev_preclimate(self, vehicle_id: str) -> GenericCorrelationIdResponse:
        logger.debug("Starting climate for %s", vehicle_id)
        user_id = self._require(self.state.user_id, "Missing user id")
        response = self._request(
            "POST",
            f"{BASE_URL}/ev/v1/vehicle/{vehicle_id}/pretripclimate/start",
            token=self._resolve_vehicle_token(vehicle_id),
            user_id_header=user_id,
        )

        return GenericCorrelationIdResponse.model_validate(self._decode_json(response))

    def stop_ev_preclimate(self, vehicle_id: str) -> GenericCorrelationIdResponse:
        logger.debug("Starting climate for %s", vehicle_id)
        user_id = self._require(self.state.user_id, "Missing user id")
        response = self._request(
            "POST",
            f"{BASE_URL}/ev/v1/vehicle/{vehicle_id}/pretripclimate/stop",
            token=self._resolve_vehicle_token(vehicle_id),
            user_id_header=user_id,
        )

        return GenericCorrelationIdResponse.model_validate(self._decode_json(response))

    def close(self) -> None:
        logger.debug("Closing HTTP session")
        self.session.close()

    def _perform_full_login(self) -> None:
        logger.info("Performing full login flow")

        self.state.mobile_session_id = str(uuid.uuid4())
        self.state.app_uuid = self.state.app_uuid or str(uuid.uuid4())

        code_verifier = secrets.token_hex(32)
        code_challenge = self._pkce_challenge(code_verifier)
        mobile_state = str(uuid.uuid4())

        start_response = self.session.get(
            f"{BASE_URL}/oidc/v1/authorize",
            params={
                "client_id": ANDROID_CLIENT_ID,
                "scope": "openid",
                "response_type": "code",
                "prompt": "login",
                "redirect_uri": REDIRECT_URI,
                "state": mobile_state,
                "code_challenge": code_challenge,
                "ui_locales": self.state.locale,
            },
            headers=self._web_headers(),
            allow_redirects=True,
            timeout=self.timeout,
        )
        start_response.raise_for_status()

        identifier_form = self._extract_form(
            start_response.text, expected_action_part="/login/identifier"
        )
        identifier_form["email"] = self.email

        identifier_response = self.session.post(
            urljoin(IDENTITY_URL, identifier_form.pop("__action")),
            data=identifier_form,
            headers=self._web_headers(referer=start_response.url, origin=IDENTITY_URL),
            allow_redirects=True,
            timeout=self.timeout,
        )
        identifier_response.raise_for_status()

        password_form = self._extract_password_submission(
            identifier_response.text, identifier_response.url
        )
        password_form["password"] = self.password

        auth_response = self.session.post(
            password_form.pop("__action"),
            data=password_form,
            headers=self._web_headers(
                referer=identifier_response.url, origin=IDENTITY_URL
            ),
            allow_redirects=False,
            timeout=self.timeout,
        )
        final_location = self._follow_redirects_for_custom_scheme(auth_response)
        if not final_location.startswith(f"{REDIRECT_URI}?"):
            raise AuthenticationError(
                "Did not receive the expected kombi redirect with authorization code"
            )

        query = parse_qs(urlparse(final_location).query)
        code = self._require(query.get("code", [None])[0], "Missing authorization code")

        token_request = AccessTokenExchangeRequest(
            code=code,
            client_id=ANDROID_CLIENT_ID,
            redirect_uri=REDIRECT_URI,
            code_verifier=code_verifier,
            grant_type="authorization_code",
        )
        token_response = self.session.post(
            f"{BASE_URL}/oidc/v1/token",
            data=token_request.model_dump(),
            headers=self._app_headers(
                content_type="application/x-www-form-urlencoded", include_auth=False
            ),
            timeout=self.timeout,
        )
        token_response.raise_for_status()

        self._store_access_token_payload(
            AccessTokenResponse.model_validate(self._decode_json(token_response))
        )

    def _try_refresh_access_token(self) -> bool:
        if self._access_token_valid():
            logger.debug("Using cached access token")
            return True

        if not self._refresh_token_valid():
            logger.debug("Refresh token is unavailable or expired")
            return False

        logger.info("Refreshing access token")

        request = RefreshTokenRequest(
            refresh_token=self._require(
                self.state.refresh_token, "Missing refresh token"
            ),
            client_id=ANDROID_CLIENT_ID,
        )

        response = self.session.post(
            f"{BASE_URL}/oidc/v1/token",
            data=request.model_dump(),
            headers=self._app_headers(
                content_type="application/x-www-form-urlencoded", include_auth=False
            ),
            timeout=self.timeout,
        )

        if response.status_code >= 400:
            logger.warning(
                "Access token refresh failed with status %s", response.status_code
            )
            return False

        self._store_access_token_payload(
            AccessTokenResponse.model_validate(self._decode_json(response))
        )
        logger.debug("Access token refresh succeeded")

        return True

    def _try_refresh_vehicle_token(self, vehicle_id: str) -> bool:
        self._try_refresh_access_token()

        if self._vehicle_token_valid(vehicle_id):
            logger.debug('Using cached vehicle token for "%s"', vehicle_id)
            return True

        logger.info('Refreshing vehicle token for "%s"', vehicle_id)

        user_id = self._require(self.state.user_id, "Missing user id")
        access_token = self._require(self.state.access_token, "Missing access token")
        id_token = self._require(self.state.id_token, "Missing id token")
        tsp = self._resolve_tsp(vehicle_id)
        spin_hash = self._resolve_spin_hash()

        request = VehicleSessionRequest(
            idToken=id_token,
            tsp=tsp,
            spinHash=spin_hash,
        )

        response = self._request(
            "POST",
            f"{BASE_URL}/ss/v1/user/{user_id}/vehicle/{vehicle_id}/session",
            json=request.model_dump(),
            token=access_token,
            user_id_header=user_id,
        )

        if response.status_code >= 400:
            logger.warning(
                'Vehicle token refresh failed for "%s" with status %s',
                vehicle_id,
                response.status_code,
            )
            return False

        self._store_vehicle_session_payload(
            vehicle_id,
            VehicleSessionResponse.model_validate(self._decode_json(response)),
        )

        return True

    def _get_spin_challenge(self) -> str:
        logger.debug("Fetching spin challenge")
        response = self._request(
            "GET",
            f"{BASE_URL}/ss/v1/user/{self._require(self.state.user_id, 'Missing user id')}/challenge",
            token=self._require(self.state.access_token, "Missing access token"),
            user_id_header=self._require(self.state.user_id, "Missing user id"),
        )
        payload = SpinChallengeResponse.model_validate(self._decode_json(response))
        return self._require(
            payload.data.challenge, "Missing challenge in challenge response"
        )

    def _resolve_spin_hash(self) -> str:
        if self.spin:
            logger.debug("Computing spin hash from fresh challenge")
            challenge = self._get_spin_challenge()
            payload = f"{challenge}.{self.spin}".encode("utf-8")
            return hashlib.sha512(payload).hexdigest()

        raise VehicleSessionError("A fresh vehicle token requires spin")

    def _resolve_tsp(self, vehicle_id: str) -> str:
        if vehicle_id not in self.state.vehicles:
            raise VehicleSessionError('Vehicle "%s" not found in state' % vehicle_id)
        return self.state.vehicles[vehicle_id].tsp

    def _resolve_vehicle_token(self, vehicle_id: str) -> str:
        logger.debug('Resolving vehicle token for "%s"', vehicle_id)
        if vehicle_id not in self.state.vehicles:
            raise VehicleSessionError('Vehicle "%s" not found in state' % vehicle_id)
        if not self._try_refresh_vehicle_token(vehicle_id):
            raise VehicleSessionError(
                'Unable to refresh token for vehicle "%s"' % vehicle_id
            )
        return self.state.vehicles[vehicle_id].token

    def _store_access_token_payload(self, payload: AccessTokenResponse) -> None:
        logger.debug("Persisting access token payload")
        now = time.time()
        self.state.access_token = payload.access_token
        self.state.id_token = payload.id_token
        self.state.refresh_token = payload.refresh_token or self.state.refresh_token
        self.state.token_type = payload.token_type or "Bearer"

        if self.state.access_token:
            self.state.access_token_expires_at = now + float(payload.expires_in)
            self.state.user_id = (
                self._jwt_claim(self.state.access_token, "sub") or self.state.user_id
            )
        if self.state.id_token:
            self.state.id_token_expires_at = now + float(payload.id_expires_in)
            self.state.email = (
                self._jwt_claim(self.state.id_token, "email") or self.state.email
            )
        if self.state.refresh_token:
            self.state.refresh_token_expires_at = now + float(
                payload.refresh_expires_in or 0
            )
        self._save_state()

    def _store_vehicle_session_payload(
        self, vehicle_id: str, payload: VehicleSessionResponse
    ) -> None:
        logger.debug("Persisting vehicle session payload for '%s'", vehicle_id)

        if vehicle_id not in self.state.vehicles:
            logger.error("Vehicle %s not found", vehicle_id)
            return

        self.state.vehicles[vehicle_id].token = payload.data.carnetVehicleToken
        self.state.vehicles[vehicle_id].expires_at = float(
            self._jwt_exp(payload.data.carnetVehicleToken)
        )

        self._save_state()

    def _request(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        token: str | None,
        user_id_header: str,
    ) -> requests.Response:
        logger.debug("HTTP %s %s", method, url)
        response = self.session.request(
            method,
            url,
            params=params,
            json=json,
            headers=self._app_headers(
                token=token,
                user_id=user_id_header,
                content_type="application/json;charset=UTF-8"
                if json is None
                else "application/json; charset=UTF-8",
            ),
            timeout=self.timeout,
        )
        try:
            response.raise_for_status()
        except requests.HTTPError:
            logger.warning(
                "HTTP %s %s failed with status %s", method, url, response.status_code
            )
            raise
        logger.debug("HTTP %s %s -> %s", method, url, response.status_code)
        return response

    def _app_headers(
        self,
        *,
        token: str | None = None,
        user_id: str | None = None,
        content_type: str = "application/json;charset=UTF-8",
        include_auth: bool = True,
    ) -> dict[str, str]:
        headers = {
            "X-Mobile-Session-Id": self.state.mobile_session_id,
            "X-User-Agent": "mobile-android",
            "X-App-Uuid": self.state.app_uuid,
            "X-User-Locale": self.state.locale,
            "X-User-Country": self.state.country,
            "X-App-Version": APP_VERSION,
            "X-App-Device-Model": DEVICE_MODEL,
            "X-App-Device-Os": DEVICE_OS,
            "User-Agent": USER_AGENT_APP,
            "Accept-Encoding": "gzip, deflate, br",
            "Content-Type": content_type,
        }
        if include_auth and token:
            headers["Authorization"] = f"Bearer {token}"
        if user_id is not None:
            headers["X-User-Id"] = user_id
        return headers

    def _web_headers(
        self, *, referer: str | None = None, origin: str | None = None
    ) -> dict[str, str]:
        headers = {
            "User-Agent": USER_AGENT_WEB,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9",
            "Upgrade-Insecure-Requests": "1",
            "X-Requested-With": "com.vw.carnet.release",
        }
        if referer:
            headers["Referer"] = referer
        if origin:
            headers["Origin"] = origin
        return headers

    def _follow_redirects_for_custom_scheme(self, response: requests.Response) -> str:
        current = response
        for _ in range(10):
            location = current.headers.get("Location")
            if not location:
                raise AuthenticationError("Expected redirect during login flow")
            if location.startswith(f"{REDIRECT_URI}?"):
                logger.debug("Received redirect back to kombi scheme")
                return location
            logger.debug("Following login redirect to %s", location)
            current = self.session.get(
                urljoin(current.url, location),
                headers=self._web_headers(referer=current.url),
                allow_redirects=False,
                timeout=self.timeout,
            )
        raise AuthenticationError("Too many redirects during login flow")

    def _extract_form(self, html: str, *, expected_action_part: str) -> dict[str, str]:
        form_pattern = re.compile(
            r"<form\b[^>]*action=\"([^\"]+)\"[^>]*>(.*?)</form>",
            re.DOTALL | re.IGNORECASE,
        )
        input_pattern = re.compile(r"<input\b([^>]+)>", re.IGNORECASE)
        attr_pattern = re.compile(r"([a-zA-Z_:][\w:.-]*)=\"([^\"]*)\"")

        for action, body in form_pattern.findall(html):
            if expected_action_part not in action:
                continue
            payload = {"__action": action}
            for input_attrs in input_pattern.findall(body):
                attrs = {
                    key.lower(): value
                    for key, value in attr_pattern.findall(input_attrs)
                }
                name = attrs.get("name")
                if not name:
                    continue
                payload[name] = attrs.get("value", "")
            return payload
        raise AuthenticationError(
            f"Could not find form with action containing {expected_action_part!r}"
        )

    def _extract_password_submission(self, html: str, page_url: str) -> dict[str, str]:
        form = self._extract_form_or_none(
            html, expected_action_part="/login/authenticate"
        )
        if form is not None:
            form["email"] = self.email
            return form

        csrf_token = self._search_required(
            r"csrf_token:\s*'([^']+)'", html, "csrf_token"
        )
        relay_state = self._search_required(
            r'relayState":"([^"]+)"', html, "relayState"
        )
        hmac = self._search_required(r'"hmac":"([^"]+)"', html, "hmac")
        email = self._search_required(r'"email":"([^"]+)"', html, "email")
        post_action = self._search_required(
            r'"postAction":"([^"]+)"', html, "postAction"
        )
        return {
            "__action": self._resolve_action_url(page_url, post_action),
            "_csrf": csrf_token,
            "relayState": relay_state,
            "email": email,
            "hmac": hmac,
        }

    def _extract_form_or_none(
        self, html: str, *, expected_action_part: str
    ) -> dict[str, str] | None:
        form_pattern = re.compile(
            r"<form\b[^>]*action=\"([^\"]+)\"[^>]*>(.*?)</form>",
            re.DOTALL | re.IGNORECASE,
        )
        input_pattern = re.compile(r"<input\b([^>]+)>", re.IGNORECASE)
        attr_pattern = re.compile(r"([a-zA-Z_:][\w:.-]*)=\"([^\"]*)\"")

        for action, body in form_pattern.findall(html):
            if expected_action_part not in action:
                continue
            payload = {"__action": urljoin(IDENTITY_URL, action)}
            for input_attrs in input_pattern.findall(body):
                attrs = {
                    key.lower(): value
                    for key, value in attr_pattern.findall(input_attrs)
                }
                name = attrs.get("name")
                if not name:
                    continue
                payload[name] = attrs.get("value", "")
            return payload
        return None

    def _decode_json(self, response: requests.Response) -> dict[str, Any]:
        try:
            return response.json()
        except ValueError as exc:
            raise VWClientError(f"Expected JSON response from {response.url}") from exc

    def _resolve_action_url(self, page_url: str, action: str) -> str:
        if action.startswith("http://") or action.startswith("https://"):
            return action
        if action.startswith("/"):
            return urljoin(IDENTITY_URL, action)

        current_no_query = page_url.split("?", 1)[0]
        if current_no_query.endswith(action):
            return current_no_query
        if action.startswith("login/"):
            base = current_no_query.rsplit("/", 1)[0]
            tail = action.split("/", 1)[1]
            return f"{base}/{tail}"
        return urljoin(f"{current_no_query.rsplit('/', 1)[0]}/", action)

    def _search_required(self, pattern: str, text: str, name: str) -> str:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if not match:
            raise AuthenticationError(f"Could not find {name} in current identity page")
        return match.group(1)

    def _load_state(self) -> VWSessionState:
        logger.debug("Loading session state from %s", self.session_path)
        if not self.session_path.exists():
            logger.debug("No existing session state found")
            return VWSessionState()
        try:
            return VWSessionState.from_json(
                json.loads(self.session_path.read_text(encoding="utf-8"))
            )
        except (OSError, json.JSONDecodeError):
            logger.warning("Failed to load session state; starting fresh")
            return VWSessionState()

    def _save_state(self) -> None:
        logger.debug("Saving session state to %s", self.session_path)
        self.session_path.parent.mkdir(parents=True, exist_ok=True)
        self.session_path.write_text(
            json.dumps(self.state.to_json(), indent=2, sort_keys=True),
            encoding="utf-8",
        )

    def _access_token_valid(self) -> bool:
        return self._token_valid(
            self.state.access_token, self.state.access_token_expires_at
        )

    def _refresh_token_valid(self) -> bool:
        return self._token_valid(
            self.state.refresh_token, self.state.refresh_token_expires_at
        )

    def _vehicle_token_valid(self, vehicle_id: str) -> bool:
        if vehicle_id not in self.state.vehicles:
            return False
        return self._token_valid(
            self.state.vehicles[vehicle_id].token,
            self.state.vehicles[vehicle_id].expires_at,
        )

    def _token_valid(self, token: str | None, expires_at: float | int | None) -> bool:
        return bool(token and expires_at and float(expires_at) > time.time() + 60)

    def _pkce_challenge(self, verifier: str) -> str:
        digest = hashlib.sha256(verifier.encode("utf-8")).digest()
        return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")

    def _jwt_claim(self, token: str, claim: str) -> Any:
        payload = self._decode_jwt_payload(token)
        return payload.get(claim)

    def _jwt_exp(self, token: str) -> int:
        payload = self._decode_jwt_payload(token)
        exp = payload.get("exp")
        if not isinstance(exp, int):
            raise VWClientError("JWT did not contain an integer exp claim")
        return exp

    def _decode_jwt_payload(self, token: str) -> dict[str, Any]:
        try:
            payload_segment = token.split(".")[1]
            payload_segment += "=" * (-len(payload_segment) % 4)
            return json.loads(
                base64.urlsafe_b64decode(payload_segment.encode("ascii")).decode(
                    "utf-8"
                )
            )
        except (IndexError, ValueError, json.JSONDecodeError) as exc:
            raise VWClientError("Failed to decode JWT payload") from exc

    def _require(self, value: Any, message: str) -> Any:
        if value in (None, ""):
            raise VWClientError(message)
        return value
