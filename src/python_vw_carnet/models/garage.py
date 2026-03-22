from pydantic import BaseModel
from typing import List


class Address(BaseModel):
    addressLine1: str
    zipCode: str
    city: str
    state: str
    country: str
    validationInd: str
    validationSource: str
    validatedOn: int


class Email(BaseModel):
    email: str
    id: int
    primary: bool


class Phone(BaseModel):
    number: str
    type: str
    id: int
    primary: bool


class User(BaseModel):
    userId: str
    idpSSOId: str
    email: str
    firstName: str
    lastName: str
    preferredLanguage: str
    localeCode: str
    address: Address
    phones: List[Phone]
    emails: List[Email]
    vwId: str
    mdmId: int
    updatedAt: int


class Activation(BaseModel):
    status: str


class Relationship(BaseModel):
    relationshipName: str
    relationshipStatus: str
    termsOfServiceStatus: str


class Vehicle(BaseModel):
    vehicleId: str
    brand: str
    modelName: str
    modelYear: int
    modelCode: str
    modelDesc: str
    tspProvider: str
    representativeImgURLPartial: str
    representativeImgURLComplete: str
    country: str
    stolenFlag: str
    carnetEnabled: bool
    carnetUserRole: str
    preferred: bool
    isMostRecentAccessedVehicle: bool
    redemptionPeriod: bool
    paintColorCode: str
    relationships: List[Relationship]
    vin: str
    activation: Activation
    status: str
    enrollmentStartDate: int


class Data(BaseModel):
    profileStatus: str
    spinStatus: str
    vehicles: List[Vehicle]
    user: User
    callToActions: List[str]


class GarageResponse(BaseModel):
    data: Data
