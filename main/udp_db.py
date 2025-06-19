import json
import logging
import os
import time
import dotenv
import requests


from ast import literal_eval
from .udp_broadcast import UDPBroadcastController
from .i2cmonitor import I2CMonitorController
from .ltemonitor import LTEMonitorController

dotenv.load_dotenv()

udp_db = None

class UDP_DB:

    def __init__(self, interfaces, port):
        self._db = dict()
        self.udp_broadcast = UDPBroadcastController(interfaces, port, module_name="WEBDOC",
                                                    callback=self.udp_callback,
                                                    poll_interval=.5,
                                                    start=True)
        self._db['_version'] = 0
        self._db['vpn_ip'] = os.getenv('VPN_IP', "")

    def udp_callback(self, msg):

        try:
            logging.info(f"UDP DB Rx Message:{msg}")
            vector = msg.split(':', 2)
            self.save_value(vector[:-1], vector[-1])
        except:
            logging.error("Could not save in database")

    def save_value(self, keys, value, expiration=0):
        db = self._db
        for key in keys:
            if key not in db:
                db[key] = dict()
            db = db[key]

        if 'value' not in db:
            db['value'] = dict()
            db['value']['version'] = -1

        db['value']['value'] = value
        db['value']['timestamp'] = int(time.time())
        db['value']['expiration'] = expiration
        db['value']['version'] += 1
        logging.info(f"Saving {value} at {keys}")
        self._db['_version'] += 1

    def get_value(self, key_str):

        try:
            db = self._db
            if ':' not in key_str:
                return db[key_str]

            key_vector = key_str.split(':', 2)
            for key in key_vector:
                db = db[key]

            value = db['value']['value']
            return value
        except Exception as e:
            logging.error(f"Error retrieving db value {key_vector} {e}")
            return None

    def get_value_dict(self, key_str):
        try:
            value = self.get_value(key_str)
            if value is None:
                return None
            value_dict = json.loads(value)
            return value_dict
        except Exception as e:
            logging.error(f"Error retrieving db value {keys} {e}")
            return value

    def remove_key(self, keys):
        db = udp_db
        try:
            for key in keys[:-1]:
                db = db[key]

            del db[keys[-1]]
        except:
            pass



    def db_str(self):
        return json.dumps(self._db, indent=3)

    def update(self):
        self.udp_broadcast.poll()

    def send_msg(self, msg):
        udp_db.udp_broadcast.udp_tx_broadcast(msg, module_name="")

    def save_building_info(self, name, address, phone_number, photo=None):
        global udp_db

        self.save_value(["building", "name"], name)
        self.save_value(["building", "address"], address)
        self.save_value(["building", "phone_number"], phone_number)
        if photo:
            self.save_value(["building", "photo"], photo)

port = int(os.getenv("UDP_PORT", "1120"))
try:
    default_interfaces = '["end0", "docker0"]'
    udp_interfaces = os.getenv("UDP_INTERFACES", default_interfaces)
    interfaces = literal_eval(udp_interfaces)
except Exception as e:
    print(e)
    interfaces = default_interfaces




def get_building_info():
    vpn_ip = os.getenv('VPN_IP')
    url = f"https://dev.nextgen.visibleaccess.net/field/building_info"
    r = requests.get(url, params={"ip": vpn_ip})
    if r.status_code == 200:
        try:
            info = json.loads(r.text)
            udp_db.save_building_info(info['name'], info['address'], info['phone_number'],
                                      photo=info['photo'])
        except:
            logging.info(f"Error parsing building info {r.text}")



logging.basicConfig(level=logging.DEBUG)

udp_db = UDP_DB(interfaces, port)
i2c_monitor = I2CMonitorController(udp_broadcast=udp_db.udp_broadcast, poll_interval=60, start=True)
lte_monitor = LTEMonitorController(udp_broadcast=udp_db.udp_broadcast, poll_interval=30, start=True)

get_building_info()

if __name__ == "__main__":
    logger_name = os.getenv("DOCWEB_LOGGER", "docweb")
    logger = logging.getLogger(logger_name)

    while True:
        udp_db.update()
        time.sleep(1)
