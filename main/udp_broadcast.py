import socket
import netifaces
import logging
import os
import select
import sys
import threading
import time
from ast import literal_eval
import argparse




class UDPBroadcastController:
    def __init__(self, interfaces, port, poll_interval=None, callback=None, start=False, module_name=None,
                 keep_alive_msg="PING", keep_alive_interval=10):
        self._udp_socket = None
        self._udp_ip_list = list()
        self._udp_port =port
        self._callback_function = callback
        self._poll_interval = poll_interval
        self._create_udp_sockets(interfaces, port)
        self._module_name = module_name
        self._kill_thread = False
        self._thread = None
        self._keep_alive_interval= keep_alive_interval
        self._next_keep_alive_send = 0
        self._keep_alive_expiration = self._compute_keep_alive_expiration_time()
        self._keep_alive_msg = keep_alive_msg

        if start is True:
            self.start()

    def set_callback(self, callback):
        self._callback_function = callback
    def _compute_keep_alive_expiration_time(self):
        return int(time.time() + (6 * self._keep_alive_interval))

    def _ip_addr_by_inet_name(self, inet_name):
        addresses = netifaces.ifaddresses(inet_name)
        for key in addresses:
            for value in addresses[key]:
                try:
                    if value['addr'] == "127.0.0.1":
                        return value['peer']
                    if "netmask" in value:
                        return value['broadcast']
                except:
                    continue

        return None

    def _create_udp_sockets(self, interfaces, port):
        try:
            # Configure receive socket for UDP
            ip_addr = "0.0.0.0"
            logging.info(f'Creating UDP socket on {ip_addr}:{port}')
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)  # UDP
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            sock.bind((ip_addr, self._udp_port))
            self._udp_socket = sock

            # Now extract the transmit sockets IP addresses
            for inet_name in interfaces:
                try:
                    broadcast_ip_addr = self._ip_addr_by_inet_name(inet_name)
                    if broadcast_ip_addr is not None:
                        self._udp_ip_list.append(broadcast_ip_addr)
                        logging.info(f"Setting {broadcast_ip_addr} as broadcast address for {inet_name}")
                    else:
                        logging.error(f"Could not determine udp broadcast address for {inet_name}")
                except:
                    logging.error(f"Could not determine udp broadcast address for {inet_name}")


        except Exception as e:
            logging.error(e)
            pass

    def udp_rx_messages(self):
        if self._udp_socket is None:
            return

        message_list = list()
        try:
            while True:
                readable, writeable, exceptional = select.select([self._udp_socket], [], [], 0)

                if not readable:
                    break

                try:
                    msg = self._udp_socket.recv(1024).decode('utf-8')
                    if f"{self._module_name}:" in msg:
                        continue
                    logging.info(f"UDP Rx message: {msg}")

                    if "PING" in msg:
                        if self._module_name not in msg:
                            #logging.info("PING received, resetting keep alive expiration")
                            self._keep_alive_expiration = self._compute_keep_alive_expiration_time()
                            continue

                    message_list.append(msg)
                except Exception as e:
                    logging.error(e)


        except Exception as e:
            logging.error(e)

        return message_list



    def udp_tx_broadcast(self, msg, module_name=None):
        try:
            if module_name == "":
                udp_msg = msg
            elif module_name is not None:
                udp_msg = f"{module_name}:{msg}"
            elif self._module_name is not None:
                udp_msg = f"{self._module_name}:{msg}"
            else:
                udp_msg = msg

            for broadcast_ip_addr in self._udp_ip_list:
                self._udp_socket.sendto(udp_msg.encode('utf-8'), (broadcast_ip_addr, int(self._udp_port)))
                logging.info(f"UDP Send: {broadcast_ip_addr}:{self._udp_port} - {udp_msg}")

            if "PANIC:" in msg:
                time.sleep(.5)
                sys.exit(86)

        except Exception as e:
            logging.error(e)
            pass


    def start(self, poll_interval=None):
        if poll_interval:
            self._poll_interval = poll_interval

        if self._poll_interval:
            self._thread = (threading.Thread(target=self._udp_thread))
            self._thread.start()


    def _send_callback(self, message_list):

            if self._callback_function:
                try:
                    for msg in message_list:
                        self._callback_function(msg)
                except Exception as e:
                    pass

    def kill_thread(self):
        self._kill_thread = True

    def keepalive(self):
        if self._keep_alive_interval:
            now = time.time()
            if now > self._next_keep_alive_send:
                self._next_keep_alive_send = now + self._keep_alive_interval
                self.udp_tx_broadcast(self._keep_alive_msg)

    def poll(self):
        message_list = self.udp_rx_messages()
        if message_list:
            self._send_callback(message_list)

        self.keepalive()

        now = int(time.time())
        if now >  self._keep_alive_expiration:
            #logging.error(f"Fatal error, keep alive time expired, exit and restart")
            self._keep_alive_expiration = self._compute_keep_alive_expiration_time()



    def _udp_thread(self):
        self.thread_id = threading.get_native_id()
        logging.info(f"UDPBroadcastController starting thread {self.thread_id}")

        while self._kill_thread is False:
            self.poll()
            time.sleep(self._poll_interval)

        logging.info("Exiting UDPBroadcastController...")


    def is_alive(self):
        if self._thread is None:
            return True
        return self._thread.is_alive()

port = int(os.getenv("UDP_PORT", "1120"))
try:
    udp_interfaces = os.getenv("UDP_INTERFACES", '["lo", "end0", "docker0"]')
    interfaces = literal_eval(udp_interfaces)
except Exception as e:
    print(e)
    interfaces = ["lo", "end0", "docker0"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--udp_port",  type=int, help="udp broadcast port", default=1120)
    parser.add_argument("-i", "--interfaces", type=str, help="udp interfaces", default='["lo", "end0"]')
    parser.add_argument("-m", "--module", type=str, help="module name", default="ATA")
    parser.add_argument("-k", "--keepalive", type=str, help="keepalive message", default="PING")
    args = parser.parse_args()


    udp_port = args.udp_port
    try:
        interfaces = literal_eval(args.interfaces)
    except:
        interfaces = ["lo", "end0"]

    udp_controller = UDPBroadcastController(module_name=args.module, interfaces=interfaces, port=args.udp_port,
                                            poll_interval=.1, keep_alive_msg=args.keepalive)

    udp_controller.start()

    while True:
        q = input()
        udp_controller.udp_tx_broadcast(q)