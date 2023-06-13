# Path: config/config_handler.py
import json


class ConfigHandler:
    def __init__(self, config_file):
        self.config_file = config_file
        self.config = self.load_configuration()

    def load_configuration(self):
        with open(self.config_file, 'r') as file:
            configuration = json.load(file)
        return configuration

    def get_config(self, key):
        return self.config.get(key, None)
