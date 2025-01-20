class DefaultConfiguration:
    def __init__(self):
        self.verbose = False
        self.connectivity_check_url = ""
        self.proxy_status_table = []
        self.delay_connectivity_check = 4  # 4 seconds
        self.delay_proxy_selection = 4  # 3 seconds
        self.iptables_latest_selected_key = ""

        self.dokodemo_enabled = True
        self.iptables_inbound_interface = "proxy"  # interface name

        self.http_enabled = True
        self.http_apply_to_source = "0.0.0.0"  # or an ip address
        self.http_inbound_port = 4001


default_config = DefaultConfiguration()

default_config.verbose = True
default_config.connectivity_check_url = "https://google.com"

# dokodemo port is the key
default_config.proxy_status_table = dict()
default_config.proxy_status_table["unique name 1"] = {
    "dokodemo_port": 12345,
    "comment": "first proxy",
    "status": "down",
    "priority": 1,
    "connectivity_test": "http://127.0.0.1:10000",
    "http_ip": "127.0.0.1",  # proxy port 4001 to port 6000 tcp
    "http_port": 6000,
}
default_config.proxy_status_table["unique name 2"] = {
    "dokodemo_port": 23456,
    "comment": "second proxy",
    "status": "down",
    "priority": 2,
    "connectivity_test": "http://127.0.0.1:20000",
    "http_ip": "127.0.0.1",  # proxy port 4001 to port 7000 tcp
    "http_port": 7000,
}
