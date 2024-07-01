import os
import sys

class DefaultConfiguration:
    def __init__(self):
        self.verbose = False
        self.connectivity_check_url = ""
        self.proxy_status_table = []
        self.delay_connectivity_check = 4 # 4 seconds
        self.delay_proxy_selection = 4 # 3 seconds
        self.iptables_target_port = -1
        self.iptables_inbound_interface = "proxy" # interface name

default_config = DefaultConfiguration()

default_config.verbose = True
default_config.connectivity_check_url = "https://google.com"

# dokodemo port is the key
default_config.proxy_status_table = dict()
default_config.proxy_status_table["unique name 1"] = 
        {
            "dokodemo_port": 12345
            "comment": "first proxy",
            "status": "down",
            "priority": 1,
            "connectivity_test": "http://127.0.0.1:10000",
        }
default_config.proxy_status_table["unique name 2"] = 
        {
            "dokodemo_port": 23456
            "comment": "second proxy",
            "status": "down",
            "priority": 2,
            "connectivity_test": "http://127.0.0.1:20000",
        }
