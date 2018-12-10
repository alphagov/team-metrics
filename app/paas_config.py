import os
import json


def extract_paas_config():
    vcap_services = json.loads(os.environ['VCAP_SERVICES'])
    set_config_env_vars(vcap_services)


def set_config_env_vars(vcap_services):
    os.environ['SQLALCHEMY_DATABASE_URI'] = vcap_services['postgres'][0]['credentials']['uri']

    credentials = vcap_services['user-provided'][0]['credentials']

    for k, v in credentials.items():
        os.environ[k] = v
