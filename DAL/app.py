from DAL import DAL
import logging
import os
import sys
from load_config import load_config
load_config('dal_cm')

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(os.environ['LOG_LEVEL'])
logging.basicConfig(format=os.environ['LOG_FORMAT'], stream=sys.stdout)

if __name__ == "__main__":
    dal = DAL()
    dal.run()
