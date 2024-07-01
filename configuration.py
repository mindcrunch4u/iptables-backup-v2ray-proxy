import os
import sys

class DefaultConfiguration:
    def __init__(self):
        self.verbose = False
        self.connectivity_check_url = ""
        self.proxy_status_table = []

default_config = DefaultConfiguration()

default_config.verbose = True
default_config.connectivity_check_url = "https://google.com"

default_config.proxy_status_table = [
        {
            "comment": "first proxy",
            "status": "down",
            "priority": 1,
            "connectivity_test": "http://127.0.0.1:10000",
            "dokodemo_port": 12345
        },
        {
            "comment": "second proxy",
            "status": "down",
            "priority": 2,
            "connectivity_test": "http://127.0.0.1:20000",
            "dokodemo_port": 23456
        },
        ]
