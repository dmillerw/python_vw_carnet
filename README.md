# python_vw_carnet

This library aims to provide some amount of interaction with the Volkswagen CarNet API **specific to the US. This will not work in any other country!**

This library has **not** been battle tested. It works for me on my machine and that's as far as I've gotten.

**I am not responsible for any issues resulting in your use of  this library, including but not limited to loss of account access, acts of God, or your car gaining sentience and locking you in the car, forcing you to listen to polka music on repeat.**

## What can it do?

So far, at least with the VW ID.4 I have, it can do the following:

- Retrieve vehicle status (mileage, battery, charging status, etc)

- Retrieve door/window status

- Start/stop preclimate control

## Vehicle Compatibility

This library is intended for Volkswagen vehicles in the United States that use the `myVW` application and connected services.

Volkswagen's U.S. myVW page says the app is available on most model years 2020 and newer vehicles. The table below is a practical compatibility reference derived from Volkswagen's published U.S. connected-services compatibility charts.

❔ = compatibility is unknown

❌ = no compatibility (mostly because this car doesn't exist in this year)

⚠️ = partial compatibility

✅ = full compatibility


| Model             | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|-------------------|------|------|------|------|------|------|------|
| Atlas Cross Sport | ❔    | ❔    | ❔    | ❔    | ❔    | ❔    | ❔    |
| Atlas             | ❔    | ❔    | ❔    | ❔    | ❔    | ❔    | ❔    |
| Arteon            | ❔    | ❔    | ❔    | ❔    | ❌    | ❌    |  ❌   |
| Tiguan            | ❔    | ❔    | ❔    | ❔    | ❔    | ❔    | ❔    |
| Passat            | ❔    | ❔    | ❔    | ❌    |  ❌   | ❌    | ❌    |
| Jetta             | ❔    | ❔    | ❔    | ❔    | ❔    | ❔    | ❔    |
| Jetta GLI         | ❔    | ❔    | ❔    | ❔    | ❔    | ❔    | ❔    |
| Taos              | ❌    | ❌    | ❔    | ❔    | ❔    | ❔    |      |
| Golf              | ❔    | ❔    |  ❌   | ❌    | ❌    | ❌    | ❌    |
| Golf GTI          | ❔    | ❔    | ❔    | ❔    | ❔    | ❔    | ❔    |
| Golf R            | ❌    | ❌    | ❔    | ❔    | ❔    | ❔    | ❔    |
| ID.4              | ❌    | ❔    | ❔    | c    | ❔    | ❔    | ❌    |
| ID. Buzz          | ❌    | ❌    |  ❌   | ❌    |  ❌   | ❔    | ❌    |

## Accuracy/Completeness

This library is very much a work in progress. As I said it currently suits my needs, but it is not feature complete or accurate in the slightest.

I own a 2023 VW ID.4, so I do not have a complete picture of the data available via VWs various APIs.

**I am 100% open to contributions to flesh out the library with more features/information. Open an issue or PR and let's talk :)**

## Usage

//TODO, kind of...

Information on the response types and exactly what data is available can be found in `python_vw_carnet.models`

There is a basic CLI for testing at `python_vw_carnet.__main__`

```python
from python_vw_carnet import VWClient

# Instantiate the python_vw_carnet.VWClient class
client = VWClient(
    email='', # Account email
    password='', # Account password
    spin='', # Account PIN (4 digits)
    session_path='', # Storage path for session persistence (default is $HOME/.vw_client/session.json)
)

# Retrieve Garage
client.get_garage()

# Retrieve Vehicle Information
client.get_vehicle(vehicle_id='')

# Retrieve Vehicle Location
client.get_vehicle_location(vehicle_id='')

# Retrieve EV Status Information
client.get_ev_summary(vehicle_id='', temp_unit='f')
```

## Local Development

This project uses `uv` and targets Python 3.12+.

### Set up the environment

From the repository root:

```powershell
uv sync
```

That will create `.venv` and install both runtime and development dependencies from the project configuration.
