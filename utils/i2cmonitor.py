import argparse
import logging
import os
import threading
import time
from ast import literal_eval

from mcp9808 import MCP9808
from ina226 import INA226
from udp_broadcast import UDPBroadcastController

logger = logging.getLogger("DTMFHandler")

I2C_BUS = int(os.getenv("I2C_BUS", 3))
INA226_SHUNT1_RES = float(os.getenv("INA226_SHUNT1", ".025"))

class I2CMonitorController:

    def __init__(self, interfaces, udp_port, poll_interval=None, module_name="I2CMON", start=False):

        self._poll_interval=poll_interval
        self._kill_thread = False
        self.thread_id = None

        self.udp_broadcast = UDPBroadcastController(interfaces=interfaces, port=udp_port, module_name=module_name)

        self._mcp9808 = MCP9808()
        self._ina226 = INA226(busnum=I2C_BUS, shunt_ohms=INA226_SHUNT1_RES, log_level=logging.INFO)
        self._ina226.reset()
        self._ina226.configure()

        if start is True:
            self.start()


    def start(self, poll_interval=None):
        if poll_interval:
            self._poll_interval = poll_interval

        if self._poll_interval:
            threading.Thread(target=self.i2cmonitor_thread).start()

    def poll(self):
        temperature = self._mcp9808.read_temperature()
        self.udp_broadcast.udp_tx_broadcast(f"TEMP:{temperature}")

        v1 =  self._ina226.supply_voltage()
        self.udp_broadcast.udp_tx_broadcast(f"V1:{round(v1,1)}")
        i1amps = self._ina226.current()
        self.udp_broadcast.udp_tx_broadcast(f"I1A:{round(i1amps,1)}")
        v1_shunt = self._ina226.shunt_voltage()
        self.udp_broadcast.udp_tx_broadcast(f"V1SHUNT:{round(v1_shunt,1)}")
        w1 = self._ina226.power()
        self.udp_broadcast.udp_tx_broadcast(f"W1:{round(w1)}")


    def kill_thread(self):
        self._kill_thread = True


    def i2cmonitor_thread(self):
        self.thread_id = threading.get_native_id()
        logger.info(f"I2CMonitor starting thread {self.thread_id}")

        while self._kill_thread is False:
            self.poll()
            time.sleep(self._poll_interval)

        logger.info("Exiting I2CMonitorController...")



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--audio_device", type=int,  help="set audio device index", default=3)
    parser.add_argument("-p", "--udp_port",  type=int, help="udp broadcast port", default=1120)
    parser.add_argument("-i", "--interfaces", type=str, help="udp interfaces",
                        default='["lo", "eth0", "end0", "en0"]')
    parser.add_argument("-m", "--module", type=str, help="module name", default="I2CMON")
    parser.add_argument("-k", "--keepalive", type=str, help="keepalive message", default="PING")
    args = parser.parse_args()


    try:
        interfaces = literal_eval(args.interfaces)
    except:
        interfaces = ["lo", "end0", "docker0"]

    i2cmonitor = I2CMonitorController(interfaces, args.udp_port)
    i2cmonitor.poll()
