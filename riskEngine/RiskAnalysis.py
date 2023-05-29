from abc import ABC, abstractmethod
import json
from enum import Enum
from dataclasses import dataclass,asdict
from typing import Dict
from random import random
import os
import sys
import logging
from load_config import load_config
load_config('risk_analysis_cm')

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(os.environ['LOG_LEVEL'])
logging.basicConfig(format=os.environ['LOG_FORMAT'], stream=sys.stdout)


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
    risk_state: RiskStateField = None

    def is_approved(self):
        return self.risk_state == RiskStateField.APPROVED

    def as_dict(self):
        return asdict(self)

    def __str__(self):
        return f'risk_level : {self.risk_level} risk_state : {self.risk_state}'


class AbstractRiskAnalysis(ABC):

    @abstractmethod
    def evaluate_risk(self,risk_level: float) -> bool:
        """Interface Method"""
    @abstractmethod
    def perform_risk_analysis(self, payment_message: Dict) -> RiskMessage:
        """Interface Method"""


class RiskAnalysis(AbstractRiskAnalysis):
    def evaluate_risk(self,risk_level: float) -> RiskStateField:
        return RiskStateField.APPROVED \
            if risk_level < float(os.environ['RISK_SUCCESS_THRESHOLD']) \
            else RiskStateField.REJECTED

    def perform_risk_analysis(self, payment_message: Dict) -> RiskMessage:
        raise NotImplemented


class RiskAnalysisV1(RiskAnalysis):
    def perform_risk_analysis(self, payment_message: Dict) -> RiskMessage:
        risk_level = round(random(), 2)
        risk_state = self.evaluate_risk(risk_level)
        return RiskMessage(risk_level, risk_state)


class RiskAnalysisV2(RiskAnalysis):

    def perform_risk_analysis(self, payment_message: Dict) -> RiskMessage:
        risk_level = 100 if float(payment_message.get('request').get('amount')) > 7 else 0
        risk_state = self.evaluate_risk(risk_level)
        return RiskMessage(risk_level, risk_state)


class RiskAnalysisFactory:
    @staticmethod
    def get_risk_analysis(risk_analysis_type:str):
        mapper = {'v1': RiskAnalysisV1(),
                  'v2': RiskAnalysisV2()}

        return mapper.get(risk_analysis_type)
