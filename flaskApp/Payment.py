from dataclasses import dataclass, asdict
from typing import Dict
from enum import Enum


class RequestMethod(Enum):
    POST = 'post'
    GET = 'get'


class ResponseCode(Enum):
    OK = 200
    CREATED = 201
    NOT_FOUND = 404
    BAD_REQUEST = 400


@dataclass
class PaymentRequest:
    request: Dict = None
    request_method: RequestMethod = None
    response_message: Dict = None
    response_code: ResponseCode = None
    duration: float = None

    def as_dict(self):
        return asdict(self)



