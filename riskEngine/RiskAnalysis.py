from abc import ABC, abstractmethod
import json
from enum import Enum
from dataclasses import dataclass,asdict
from load_config import load_config
from random import random
import os
import sys
import logging
from load_config import load_config
load_config('risk_analysis_cm')

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(os.environ['LOG_LEVEL'])
logging.basicConfig(format=os.environ['LOG_FORMAT'], stream=sys.stdout)


class AbstractRiskAnalysis(ABC):

    @abstractmethod
    def do_risk_analysis(self, payment_message: str) -> bool:
        """"""


class DataclassEncoder(json.JSONEncoder):
    def default(self,obj):
        if isinstance(obj, Enum):
            return obj.value
        return super().default(obj)


class RiskStateField(Enum):
    APPROVED = os.environ['APPROVED_LABEL']
    REJECTED = os.environ['REJECTED_LABEL']

@dataclass
class RiskMessage:
    risk_level: float = None
    @property
    def risk_state(self):
        return RiskStateField.APPROVED if self.risk_level < float(os.environ['RISK_SUCCESS_THRESHOLD']) \
                                        else RiskStateField.REJECTED

    def is_approved(self):
        return self.risk_state == RiskStateField.APPROVED

    def as_dict(self):
        return asdict(self)

    def __str__(self):
        return f'risk_level : {self.risk_level} risk_state : {self.risk_state}'


class RiskAnalysis(AbstractRiskAnalysis):
    def __init__(self):
        self._risk_engine_threshold = float(os.environ['RISK_SUCCESS_THRESHOLD'])

    def do_risk_analysis(self, payment_message: str) -> RiskMessage:
        risk_level = round(random(), 2)
        return RiskMessage(risk_level)
