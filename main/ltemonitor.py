import argparse
import json
import logging
import os
import subprocess
import threading
import time
from ast import literal_eval

from .udp_broadcast import UDPBroadcastController


class LTEMonitorController:

    def __init__(self, udp_broadcast=None, interfaces=None, udp_port=None, poll_interval=None,
                 module_name="LTEMONITOR", start=False):

        self._poll_interval=poll_interval
        self._kill_thread = False
        self.thread_id = None
        self._module_name = module_name
        self._need_LTE_basic_info = True

        if udp_broadcast:
            self.udp_broadcast = udp_broadcast
        else:
            self.udp_broadcast = UDPBroadcastController(interfaces=interfaces, port=udp_port, module_name=module_name)

        if start is True:
            self.start()


    def callback(self, msg):
        if ":PWRCONTROL:OFF" in msg:
            pass

        if ":PWRCONTROL:ON" in msg:
            pass

    def start(self, poll_interval=None):
        if poll_interval:
            self._poll_interval = poll_interval

        if self._poll_interval:
            threading.Thread(target=self.lte_monitor_thread).start()

    def _run_cmd(self, cmd, tag=None):
        process = subprocess.Popen(cmd, preexec_fn=os.setsid, stdout=subprocess.PIPE,
                                               stderr=subprocess.STDOUT)
        process.wait()
        try:
            response = process.stdout.read()
            return response.decode("utf-8")
        except:
            return None


    def set_interval(self):
        response = self._run_cmd(["mmcli", "-m", "0", "--signal-setup=30"])
        logging.info(f"LTE set interval response: {response}")


    def signal_get(self):
        response = self._run_cmd(["mmcli", "-m", "0", "--signal-get", "-J"])
        try:

            signal = json.loads(response)['modem']['signal']
            self.udp_broadcast.udp_tx_broadcast(f"LTE_RAW:{json.dumps(signal)}", module_name=self._module_name)
            self.udp_broadcast.udp_tx_broadcast(f"ERROR-RATE:{signal['lte']['error-rate']}", module_name=self._module_name)
            self.udp_broadcast.udp_tx_broadcast(f"RSRP:{signal['lte']['rsrp']}", module_name=self._module_name)
            self.udp_broadcast.udp_tx_broadcast(f"RSRQ:{signal['lte']['rsrq']}", module_name=self._module_name)
            self.udp_broadcast.udp_tx_broadcast(f"RSSI:{signal['lte']['rssi']}", module_name=self._module_name)
            self.udp_broadcast.udp_tx_broadcast(f"SNR:{signal['lte']['snr']}", module_name=self._module_name)
            return signal
        except Exception as e:
            return None

    def location_get(self):
        response = self._run_cmd(["mmcli", "-m", "0", "--location-get", "-J"])
        try:
            location = json.loads(response)['modem']['location']['3gpp']
            self.udp_broadcast.udp_tx_broadcast(f"CID:{location['cid']}", module_name=self._module_name)
            self.udp_broadcast.udp_tx_broadcast(f"LAC:{location['lac']}", module_name=self._module_name)
            self.udp_broadcast.udp_tx_broadcast(f"MCC:{location['mcc']}", module_name=self._module_name)
            self.udp_broadcast.udp_tx_broadcast(f"MNC:{location['mnc']}", module_name=self._module_name)
            self.udp_broadcast.udp_tx_broadcast(f"TAC:{location['tac']}", module_name=self._module_name)
            return location
        except Exception as e:
            return None

    def lte_basic_info_get(self):
        response = self._run_cmd(["mmcli", "--sim", "0", "-J"])
        try:
            info = json.loads(response)['sim']['properties']
            self.udp_broadcast.udp_tx_broadcast(f"SIM_RAW:{json.dumps(info)}", module_name=self._module_name)
            self.udp_broadcast.udp_tx_broadcast(f"OPERATOR-NAME:{info['operator-name']}", module_name=self._module_name)
            self.udp_broadcast.udp_tx_broadcast(f"ICCID:{info['iccid']}", module_name=self._module_name)
            return info
        except Exception as e:
            return None

    def poll_thread(self):
        if self._need_LTE_basic_info:
            self.set_interval()
            self.lte_basic_info_get()
            self._need_LTE_basic_info = False

        self.signal_get()
        self.location_get()

    def poll(self):
        threading.Thread(target=self.poll_thread).start()


    def kill_thread(self):
        self._kill_thread = True


    def lte_monitor_thread(self):
        self.thread_id = threading.get_native_id()
        logging.info(f"LTE starting thread {self.thread_id}")

        while self._kill_thread is False:
            self.poll()
            time.sleep(self._poll_interval)

        logging.info("Exiting LTEMonitorController...")


if __name__ == "__main__":

    logger = logging.getLogger("LTEMonitor")
    logging.basicConfig(
        format='%(asctime)s.%(msecs)03d %(levelname)-8s LTEMONITOR: %(message)s',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S')

    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--udp_port",  type=int, help="udp broadcast port", default=1120)
    parser.add_argument("-i", "--interfaces", type=str, help="udp interfaces",
                        default='["end0", "docker0"]')
    parser.add_argument("-m", "--module", type=str, help="module name", default="LTEMONITOR")
    parser.add_argument("-k", "--keepalive", type=str, help="keepalive message", default="PING")

    args = parser.parse_args()
    udp_port = args.udp_port
    try:
        interfaces = literal_eval(args.interfaces)
    except:
        interfaces = ["end0", "docker0"]


    lte_controller = LTEMonitorController(interfaces, udp_port, module_name=args.module)

    signal = lte_controller.signal_get()
    try:
        if signal['refresh']['rate'] == '0':
            lte_controller.set_interval()
            signal = lte_controller.signal_get()

    except:
        pass



