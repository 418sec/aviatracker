import os
from typing import Any, Dict

import yaml


class Config:
    def __init__(self):
        path = os.path.join(os.path.abspath(__file__ + "/../../"), "config/config.yaml")

        with open(path, "r") as config:
            parsed_yaml_file = yaml.load(config, Loader=yaml.SafeLoader)

            self.db_name = parsed_yaml_file["db"]["name"]
            self.db_user = parsed_yaml_file["db"]["user"]
            self.db_pass = parsed_yaml_file["db"]["pass"]
            self.db_host = parsed_yaml_file["db"]["host"]
            self.db_port = parsed_yaml_file["db"]["port"]

            self.websocket_allowed_origin = parsed_yaml_file["websocket"][
                "allowed_origin"
            ]

            self.opensky_user = parsed_yaml_file["opensky"]["user"]
            self.opensky_pass = parsed_yaml_file["opensky"]["pass"]

    @property
    def db_params(self) -> Dict[str, Any]:
        return {
            "name": self.db_name,
            "user": self.db_user,
            "password": self.db_pass,
            "host": self.db_host,
            "port": self.db_port,
        }


common_conf = Config()
