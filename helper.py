import json
import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def get_required_attr_from_env(key):
    if val := get_attr_from_env(key):
        return val
    else:
        raise ValueError(
            "Attribute {0}, is required to be passed as an environment variable. Please recheck template file".format(
                key))


def get_attr_from_env(key):
    return os.environ.get(key)


def get_attr_as_json_from_env(key):
    try:
        return json.loads(get_attr_from_env(key))
    except Exception as e:
        logger.warning("Can not parse json defined as env variable {0}, error = {1}".format(key, str(e)))
        return None
