from pydantic import BaseModel
from typing import List


class CruisingRange(BaseModel):
    engineType: str
    range: int


class BatteryStatus(BaseModel):
    carCapturedTimestamp: int
    currentSOCPct: int
    cruisingRange: CruisingRange
    status: str


class ChargeModeSelectionOption(BaseModel):
    chargeMode: str
    status: bool


class ChargeModeOptions(BaseModel):
    carCapturedTimestamp: int
    status: str
    chargeModeSelectionOptions: List[ChargeModeSelectionOption]


class ChargeSettings(BaseModel):
    autoUnlockPlugWhenCharged: str
    maxChargingCurrent: str
    targetSOCPercentage: int
    chargeModeSelection: str
    carCapturedTimestamp: int
    status: str


class ChargingProfileStatus(BaseModel):
    status: str


class ChargingStatus(BaseModel):
    profileChargeReason: str
    currentChargeState: str
    chargeType: str
    chargeMode: str
    chargingScenario: str
    carCapturedTimestamp: int
    chargePower: int
    chargeTargetTime: int
    status: str


class PlugStatus(BaseModel):
    carCapturedTimestamp: int
    backendCapturedTimestamp: int
    plugConnectionState: str
    plugLockState: str
    infrastructureState: str
    status: str


class BatteryAndPlugStatus(BaseModel):
    carCapturedTimestamp: int
    plugStatus: PlugStatus
    batteryStatus: BatteryStatus
    chargingStatus: ChargingStatus
    chargingProfileStatus: ChargingProfileStatus
    chargeSettings: ChargeSettings
    chargeModeOptions: ChargeModeOptions


class ClimatizationElementSettings(BaseModel):
    climatizationAtUnlock: bool
    mirrorHeatingEnabled: bool
    zoneFrontLeftEnabled: bool
    zoneFrontRightEnabled: bool
    zoneRearLeftEnabled: bool
    zoneRearRightEnabled: bool


class Temperature(BaseModel):
    temperature: int
    unit: str
    measurementState: str


class ClimateSettings(BaseModel):
    carCapturedTimestamp: int
    backendCapturedTimestamp: int
    climatizationWithoutExternalPower: bool
    targetTemperature: Temperature
    climatizationElementSettings: ClimatizationElementSettings
    status: str


class ClimateStatusReport(BaseModel):
    carCapturedTimestamp: int
    backendCapturedTimestamp: int
    remainingClimatizationTimeMin: int
    climateStatusInd: str
    trigger: str
    status: str


class TemperatureClass(BaseModel):
    carCapturedTimestamp: int
    backendCapturedTimestamp: int
    inCabinTemperature: Temperature
    outdoorTemperature: Temperature
    status: str
    statusDescription: str


class ClimateStatus(BaseModel):
    carCapturedTimestamp: int
    backendCapturedTimestamp: int
    temperature: TemperatureClass
    climateSettings: ClimateSettings
    climateStatusReport: ClimateStatusReport
    windowHeatingReport: None
    climateTimerSetting: None


class Data(BaseModel):
    batteryAndPlugStatus: BatteryAndPlugStatus
    climateStatus: ClimateStatus


class EVSummaryResponse(BaseModel):
    data: Data
