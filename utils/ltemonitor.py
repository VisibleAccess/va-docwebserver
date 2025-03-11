import argparse
import json
import logging
import os
import subprocess
import threading
import time
from ast import literal_eval

from udp_broadcast import UDPBroadcastController
from  gpio import GPIO


logger = logging.getLogger("LTEMonitor")
logging.basicConfig(
    format='%(asctime)s.%(msecs)03d %(levelname)-8s LTEMONITOR: %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')

class LTEMonitorController:

    def __init__(self, interfaces, udp_port, poll_interval=None, module_name="LTEMON", start=False):

        self._poll_interval=poll_interval
        self._kill_thread = False
        self.thread_id = None

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
            threading.Thread(target=self.i2cmonitor_thread).start()

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
        logger.info(f"LTE set interval response: {response}")

    def signal_get(self):
        response = self._run_cmd(["mmcli", "-m", "0", "--signal-get", "-J"])
        try:
            signal = json.loads(response)['modem']['signal']
            self.udp_broadcast.udp_tx_broadcast(f"RAW:{json.dumps(signal)}")
            self.udp_broadcast.udp_tx_broadcast(f"ERROR-RATE:{signal['lte']['error-rate']}")
            self.udp_broadcast.udp_tx_broadcast(f"RSRP:{signal['lte']['rsrp']}")
            self.udp_broadcast.udp_tx_broadcast(f"RSRQ:{signal['lte']['rsrq']}")
            self.udp_broadcast.udp_tx_broadcast(f"RSSI:{signal['lte']['rssi']}")
            self.udp_broadcast.udp_tx_broadcast(f"SNR{signal['lte']['snr']}")
            return signal
        except Exception as e:
            return None

    def poll_thread(self):
        self._signal_get()
        pass


    def poll(self):
        threading.Thread(target=self.poll_thread).start()



    def kill_thread(self):
        self._kill_thread = True


    def lte_monitor_thread(self):
        self.thread_id = threading.get_native_id()
        logger.info(f"LTE starting thread {self.thread_id}")

        while self._kill_thread is False:
            self.poll()
            time.sleep(self._poll_interval)

        logger.info("Exiting LTEMonitorController...")


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--udp_port",  type=int, help="udp broadcast port", default=1120)
    parser.add_argument("-i", "--interfaces", type=str, help="udp interfaces",
                        default='["lo", "eth0", "end0", "en0"]')
    parser.add_argument("-m", "--module", type=str, help="module name", default="LTEMONITOR")
    parser.add_argument("-k", "--keepalive", type=str, help="keepalive message", default="PING")

    args = parser.parse_args()
    udp_port = args.udp_port
    try:
        interfaces = literal_eval(args.interfaces)
    except:
        interfaces = ["lo", "eth0"]


    lte_controller = LTEMonitorController(interfaces, udp_port, module_name=args.module)

    signal = lte_controller.signal_get()
    try:
        if signal['refresh']['rate'] == '0':
            lte_controller.set_interval()
            signal = lte_controller.signal_get()

    except:
        pass



