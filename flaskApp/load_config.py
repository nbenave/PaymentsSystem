import json
import os
from typing import Dict
import yaml
from dotenv import load_dotenv
load_dotenv()

def load_config_into_env(_dict: Dict):
    for key, value in _dict.items():
        os.environ[key] = str(value)

def load_config(cm_file):
    cfg_path = f'k8s_files/{cm_file}.yaml'
    with open(cfg_path) as f:
        dict_config = yaml.load(f,Loader=yaml.FullLoader).get('data')
        load_config_into_env(dict_config)

def load_schema():
    cfg_path = 'k8s_files/jsonschema.yaml'
    with open(cfg_path) as f:
        json_schema_string = yaml.load(f,Loader=yaml.FullLoader).get('data').get('config.json')
        return json.loads(json_schema_string)
