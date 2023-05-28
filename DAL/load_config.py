import os
import yaml
from typing import Dict
from dotenv import load_dotenv
load_dotenv()

def load_config_into_env(_dict: Dict):
    for key, value in _dict.items():
        os.environ[key] = str(value)


def load_config(cm_file,local=True):
    cfg_path = f'k8s_files/{cm_file}.yaml'
    with open(cfg_path) as f:
        dict_config = yaml.load(f,Loader=yaml.FullLoader).get('data')
        load_config_into_env(dict_config)

