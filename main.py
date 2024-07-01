from threading import Thread, Lock
from configuration import default_config as conf
from datetime import datetime
from subprocess import Popen, PIPE, STDOUT
import time

global_mutex = Lock()
table_update_mutex = Lock()
previous_port = -1

def t():
    now = datetime.now() # current date and time
    date_time = now.strftime("%Y/%m/%d %H:%M:%S")
    return date_time

def debug(content):
    if not conf.verbose:
        return
    print("[{:19}] [~] {}".format(t(), content))

def info(content):
    print("[{:19}] [*] {}".format(t(), content))

def error(content):
    print("[{:19}] [-] {}".format(t(), content))

def build_iptables_command(inbound_interface, to_dokodemo_port, http_port=None, option="add"):
    iptables_commands = []
    iptables_action_keyword = "-A"
    if option == "add":
        iptables_action_keyword = "-A"
    else:
        # == remove
        iptables_action_keyword = "-D"

    if conf.dokodemo_enabled:
        iptables_command_tcp = "sudo iptables -t nat {} PREROUTING -i {} -p tcp -j REDIRECT --to-port {}".format(iptables_action_keyword, inbound_interface, to_dokodemo_port)
        iptables_command_udp = "sudo iptables -t nat {} PREROUTING -i {} -p udp -j REDIRECT --to-port {}".format(iptables_action_keyword, inbound_interface, to_dokodemo_port)
        iptables_commands.append(iptables_command_tcp)
        iptables_commands.append(iptables_command_udp)

    if conf.http_enabled and http_port:
        iptables_command_http = "sudo iptables -t nat {} PREROUTING -p tcp --dport {} -j REDIRECT --to-port {}".format(iptables_action_keyword, conf.http_inbound_port, http_port)
        iptables_commands.append(iptables_command_http)

    return iptables_commands

def iptables_add_route(inbound_interface, to_dokodemo_port, to_http_port=None):
    commands = build_iptables_command(inbound_interface, to_dokodemo_port, to_http_port, "add")
    for iptables_command in commands:
        process = Popen(iptables_command , stdout=PIPE, stderr=STDOUT, shell=True)
        exitcode = process.wait()
        if exitcode != 0:
            error("Failed to add iptables routes from interface {} to port {}".format(
                inbound_interface, to_dokodemo_port))
    debug("Executed all iptables commands to add routes from interface {} to port{}".format(
                inbound_interface, to_dokodemo_port))

def iptables_remove_route(inbound_interface, to_dokodemo_port, to_http_port=None):
    commands = build_iptables_command(inbound_interface, to_dokodemo_port, to_http_port, "remove")
    for iptables_command in commands:
        exitcode = 0
        while exitcode == 0:
            process = Popen(iptables_command , stdout=PIPE, stderr=STDOUT, shell=True)
            exitcode = process.wait()
            # if there is no more matching routes, then exitcode will be 1
    debug("Removed all iptables routes from interface {} to port {}".format(
            inbound_interface, to_dokodemo_port))

def build_curl_command(curl_proxy, curl_target):
# make sure that cURL has Silent mode (--silent) activated
# otherwise we receive progress data inside err message later
    if curl_proxy and len(curl_proxy.strip()) > 0:
        # has proxy
        curl_command = r"""curl -x {} --silent {}""".format(curl_proxy, curl_target)
    else:
        # no proxy configured
        curl_command = r"""curl --silent {}""".format(curl_target)
    return curl_command

def is_proxy_valid(curl_proxy, proxy_target):
    curl_command = build_curl_command(curl_proxy, proxy_target)
    process = Popen(curl_command , stdout=PIPE, stderr=STDOUT, shell=True)
    exitcode = process.wait()
    return exitcode == 0

def thread_table_update(dokodemo_port, curl_proxy, proxy_target):
    # perform curl check
    if conf.verbose:
        debug("\tupdate thread: port:{} proxy:{} target:{}".format(
            dokodemo_port, curl_proxy, proxy_target))
    result = is_proxy_valid(curl_proxy, proxy_target)
    
    table_update_mutex.acquire()
    if result:
        conf.proxy_status_table[dokodemo_port]["status"] = "up"
    else:
        conf.proxy_status_table[dokodemo_port]["status"] = "down"
    table_update_mutex.release()

def thread_connectivity_check():
    info("Connectivity Check Thread Started.")
    while True:
        global_mutex.acquire()
        debug("Checking connectivity")
        current_query_list = []
        for proxy in conf.proxy_status_table:
            current_item = {
                    "dokodemo_port": conf.proxy_status_table[proxy]["dokodemo_port"],
                    "curl_proxy": conf.proxy_status_table[proxy]["connectivity_test"],
                    "curl_target": conf.connectivity_check_url
                    }
            current_query_list.append(current_item)
        curl_threads = []
        for proxy in current_query_list:
            current_thread = Thread(target=thread_table_update, args=(
                proxy["dokodemo_port"],
                proxy["curl_proxy"],
                proxy["curl_target"]
                ))
            curl_threads.append(current_thread)
        for t in curl_threads:
            t.start()
        for t in curl_threads:
            t.join()
        if conf.verbose:
            table_update_mutex.acquire()
            debug("Table update complete.")
            for item in conf.proxy_status_table:
                debug("\tport:{} c:{} s:{} pri:{} url:{}".format(
                        conf.proxy_status_table[item]["dokodemo_port"],
                        conf.proxy_status_table[item]["comment"],
                        conf.proxy_status_table[item]["status"],
                        conf.proxy_status_table[item]["priority"],
                        conf.connectivity_check_url
                        ))
            table_update_mutex.release()
        global_mutex.release()
        time.sleep(conf.delay_connectivity_check)

def thread_proxy_selection():
    info("Proxy Selection Thread Started.")
    while True:
        global_mutex.acquire()
        table_update_mutex.acquire()
        debug("Reading proxy table.")
        sorted_list = sorted(
                conf.proxy_status_table.items(),
                key=lambda x: x[1]['priority'],
                reverse=False)
        if conf.verbose:
            debug("Sorted proxy table:")
            for item in sorted_list:
                debug("\t{}".format(item))
        selection_port = -1
        selected_unique_key = ""
        for item in sorted_list:
            current_info = item[1]
            if current_info["status"] == "up":
                selection_port = current_info["dokodemo_port"]
                selected_unique_key = item[0]
                break
            else:
                continue
        debug("Selection port:{}".format(selection_port))
        if (selection_port == None) or selection_port == -1:
            error("No heathly proxy found")
        elif selection_port <= 0:
            error("Weird port number selected")
        else:
            if conf.iptables_latest_selected_key == selected_unique_key:
                # port didn't change
                pass
            else:
                iptables_last_target_port = -1
                if conf.iptables_latest_selected_key not in conf.proxy_status_table:
                    pass
                else:
                    iptables_last_target_port = conf.proxy_status_table[conf.iptables_latest_selected_key]["dokodemo_port"]


                info("Port switched from {} to {}".format(iptables_last_target_port, selection_port))

                if iptables_last_target_port > 0:
                    info("Remove iptables rules to {}".format(iptables_last_target_port))
                    to_http_port = None
                    if "http_port" in conf.proxy_status_table[conf.iptables_latest_selected_key]:
                        to_http_port = conf.proxy_status_table[conf.iptables_latest_selected_key]["http_port"]
                    iptables_remove_route(conf.iptables_inbound_interface, iptables_last_target_port, to_http_port)

                info("Add iptables rules to {}".format(selection_port))
                to_http_port = None
                if "http_port" in conf.proxy_status_table[selected_unique_key]:
                    to_http_port = conf.proxy_status_table[selected_unique_key]["http_port"]
                iptables_add_route(conf.iptables_inbound_interface, selection_port, to_http_port)

                conf.iptables_latest_selected_key = selected_unique_key

        table_update_mutex.release()
        global_mutex.release()
        time.sleep(conf.delay_proxy_selection)

def main():
    # launch connectivity check thread
    t_check = Thread(target = thread_connectivity_check)
    # launch proxy selection thread
    t_proxy = Thread(target = thread_proxy_selection)

    t_check.start()
    t_proxy.start()

    t_check.join()
    t_proxy.join()

    info("Abort.")

if __name__ == "__main__":
    main()
