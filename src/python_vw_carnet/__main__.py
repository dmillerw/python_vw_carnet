import argparse
import os
import sys

from .client import VWClient


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Query captured myVW endpoints")
    parser.add_argument(
        "command",
        choices=["garage", "status", "location", "ev-summary"],
        help="Which payload to fetch",
    )
    parser.add_argument("--email", default=os.getenv("VW_EMAIL"))
    parser.add_argument("--password", default=os.getenv("VW_PASSWORD"))
    parser.add_argument("--spin", default=os.getenv("VW_SPIN"))
    parser.add_argument("--session-path", default=os.getenv("VW_SESSION_PATH"))
    parser.add_argument("--vehicle-id")
    parser.add_argument("--temp-unit", default="f")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if not args.email or not args.password:
        parser.error(
            "email and password are required, either as flags or via VW_EMAIL/VW_PASSWORD"
        )

    client = VWClient(
        email=args.email,
        password=args.password,
        spin=args.spin,
        session_path=args.session_path,
    )

    try:
        if args.command == "garage":
            payload = client.get_garage()
        elif args.command == "status":
            payload = client.get_vehicle(vehicle_id=args.vehicle_id)
        elif args.command == "location":
            payload = client.get_vehicle_location(vehicle_id=args.vehicle_id)
        else:
            payload = client.get_ev_summary(
                vehicle_id=args.vehicle_id, temp_unit=args.temp_unit
            )

        sys.stdout.write(payload.model_dump_json(indent=4))
        sys.stdout.write("\n")
        return 0
    finally:
        client.close()


if __name__ == "__main__":
    raise SystemExit(main())
