from RiskEngine import RiskEngine
import logging
import os
import sys
from load_config import load_config
load_config('risk_engine_cm')

logger = logging.getLogger(__name__)
logger.setLevel(os.environ['LOG_LEVEL'])
logging.basicConfig(format=os.environ['LOG_FORMAT'], stream=sys.stdout,level=logging.DEBUG)

if __name__ == "__main__":
    risk_engine = RiskEngine()
    risk_engine.run()
