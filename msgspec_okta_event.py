from __future__ import annotations

import functools
from typing import Optional
import msgspec


class Actor(msgspec.Struct):
    id: str
    type: str
    alternateId: str
    displayName: str
    detailEntry: Optional[dict]


class Target(msgspec.Struct):
    id: str
    type: str
    alternateId: str
    displayName: str
    detailEntry: dict


class UserAgent(msgspec.Struct):
    browser: Optional[str]
    os: Optional[str]
    rawUserAgent: Optional[str]


class Geolocation(msgspec.Struct):
    lat: float
    lon: float


class Outcome(msgspec.Struct):
    result: str
    reason: Optional[str]


class Transaction(msgspec.Struct):
    id: Optional[str]
    type: Optional[str]
    detail: Optional[dict]


class DebugContext(msgspec.Struct):
    debugData: Optional[dict]


class Issuer(msgspec.Struct):
    id: Optional[str]
    type: Optional[str]


class SecurityContext(msgspec.Struct):
    asNumber: Optional[int]
    asOrg: Optional[str]
    isp: Optional[str]
    domain: Optional[str]
    isProxy: Optional[bool]


class GeographicalContext(msgspec.Struct):
    geolocation: Optional[Geolocation]
    city: Optional[str]
    state: Optional[str]
    country: Optional[str]
    postalCode: Optional[str]


class AuthenticationContext(msgspec.Struct):
    authenticationProvider: Optional[str]
    authenticationStep: Optional[int]
    credentialProvider: Optional[str]
    credentialType: Optional[str]
    issuer: Optional[Issuer]
    externalSessionId: Optional[str]
    interface: Optional[str]


class Client(msgspec.Struct):
    id: Optional[str]
    userAgent: Optional[UserAgent]
    geographicalContext: Optional[GeographicalContext]
    zone: Optional[str]
    ipAddress: Optional[str]
    device: Optional[str]


class IpAddress(msgspec.Struct):
    ip: Optional[str]
    geographicalContext: Optional[GeographicalContext]
    version: Optional[str]
    source: Optional[bool]


class Request(msgspec.Struct):
    ipChain: Optional[list[IpAddress]]


class OktaEvent(msgspec.Struct):
    uuid: str
    published: str
    eventType: str
    version: str
    severity: str
    legacyEventType: Optional[str]
    displayMessage: Optional[str]
    actor: Optional[Actor]
    client: Optional[Client]
    request: Optional[Request]
    outcome: Optional[Outcome]
    target: Optional[list[dict]]
    transaction: Optional[Transaction]
    debugContext: Optional[DebugContext]
    authenticationContext: Optional[AuthenticationContext]
    securityContext: Optional[SecurityContext]


class OktaEvents(msgspec.Struct):
    events: list[OktaEvent]


loads = msgspec.json.Decoder(list[OktaEvent]).decode
load_single_event = msgspec.json.Decoder(OktaEvent).decode
dumps = msgspec.json.Encoder().encode


def r_getattr(obj, attr, *args):
    def _getattr(obj, attr):
        return getattr(obj, attr, *args)

    return functools.reduce(_getattr, [obj] + attr.split('.'))
