Implemented with `dokodemo` inbound of V2ray, and `iptables` to achieve "back up" proxy.

The main proxy port will be used for most of the connections, but when the tool detects connectivity issue, it issues `iptables` command to swtich the port to the backup proxy port.

The port priority ranges from 1 (highest) to n (lowest). Ports with high priority will be selected if there is connectivity.

In order to test connectivity of proxies, each v2ray configuration needs to expose a HTTP port locally, which will then be utilized by the script. See `configuration.py`

This tool assumes the topology below:

![setup for this script](https://github.com/mindcrunch4u/iptables-backup-v2ray-proxy/blob/main/about/topology.png)

And it works like this:

![how it updates proxy](https://github.com/mindcrunch4u/iptables-backup-v2ray-proxy/blob/main/about/how%20it%20works.png)
