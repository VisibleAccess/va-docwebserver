import cryptocode
import dotenv
import subprocess
import netifaces
import re
import os
import json
import requests
import time

from pathlib import Path

dotenv.load_dotenv()
try:
    env_file_directory = os.path.dirname(os.path.abspath(__file__))
    dotenv.load_dotenv(os.path.join(env_file_directory, ".magic"))
except:
    pass



    current_directory = Path.cwd()
    print(current_directory)


class CAMERA_INFO:
    def __init__(self, username, password, ip_address="10.11.20.50"):
        self.info = dict()
        self.ip_address = ip_address
        self.username = username
        self.password = password
        return

    def gather_all(self, info):
        try:
            info['CAMERA'] = dict()
            t = int(time.time())
            url = f"http://{self.username}:{self.password}@{self.ip_address}/cgi-bin/web.cgi?mod=device&cmd=get&_={t}"
            response = requests.get(url, timeout=2)
            device_info = json.loads(response.text)
            url = f"http://{self.username}:{self.password}@{self.ip_address}/cgi-bin/web.cgi?mod=net&cmd=get&_={t}"
            response = requests.get(url, timeout=2)
            net_info = json.loads(response.text)
            info['CAMERA']['device_type'] = device_info['devtype']
            info['CAMERA']['serial_number'] = device_info['serial_num']
            info['CAMERA']['mac_address'] = net_info['mac']
            info['CAMERA']['sw_version'] = device_info['version']

        except Exception as e:
            pass




class LTE_INFO:
    def __init__(self):
        self.info = dict()
        return

    def _run_cmd(self, cmd, tag=None):
        process = subprocess.Popen(cmd, preexec_fn=os.setsid, stdout=subprocess.PIPE,
                                               stderr=subprocess.STDOUT)
        process.wait()
        try:
            response = process.stdout.read()
            return response.decode("utf-8")
        except:
            return None



    def gather_all(self, info):
        try:
            response = self._run_cmd(["mmcli", "--sim", "0", "-J"])
            sim_response = json.loads(response)['sim']['properties']


            response = self._run_cmd(["mmcli", "-m", "0", "-J"])
            modem_response = json.loads(response)['modem']['generic']

            info['SIM'] = dict()
            info['LTE'] = dict()
            info['SIM']['iccid'] = sim_response['iccid']
            info['SIM']['phone'] = modem_response['own-numbers'][0]
            info['LTE']['imsi'] = sim_response['imsi']
            info['LTE']['imei'] = modem_response['equipment-identifier']

        except Exception as e:
            pass


class DOC_INFO:
    def __init__(self, device_type="DOC-1"):
        self.dmesg = self.get_dmesg()
        self.info = dict()
        self.device_type = device_type
        return

    def get_dmesg(self):
        result = subprocess.run(['dmesg'], capture_output=True, text=True, check=True)
        messages = result.stdout
        return messages

    def get_SD_card_size(self):
        sd_card = re.search(r"mmcblk.*?:.*?:.*? (.*?) (.*)", self.dmesg)
        size = sd_card.group(2)
        return size

    def get_serial_number(self):
        result = subprocess.run(['cat', '/proc/device-tree/serial-number'], capture_output=True, text=True, check=True)
        serial_number = result.stdout.strip('\x00')
        return serial_number

    def get_MAC(self, interface_name):
        try:
            interface = netifaces.ifaddresses(interface_name)
            mac_address = interface[17][0]['addr'].upper()
            return mac_address
        except:
            return None

    def get_IP(self, interface_name):
        try:
            interface = netifaces.ifaddresses(interface_name)
            ip_address = interface[2][0]['addr'].upper()
            return ip_address
        except:
            return None


    def gather_all(self, info):
        info['CPE'] = dict()
        info['CPE']['device_type'] = self.device_type
        info['CPE']['serial_number'] = self.get_serial_number()
        info['CPE']['sd_card_size'] = self.get_SD_card_size()
        info['CPE']['eth_mac_address']= self.get_MAC("end0")
        info['CPE']['wifi_mac_address'] = self.get_MAC("wlan0")
        info['CPE']['vpn_ip_address'] = self.get_IP("wg0")
        return



#enc_username = (camera_username,magic)
#enc_password = cryptocode.encrypt(camera_password,magic)

def register_device(host, magic):
    cypher_username = os.getenv("CAMERA_USERNAME")
    cypher_password = os.getenv("CAMERA_PASSWORD")

    camera_username = cryptocode.decrypt(cypher_username, magic)
    camera_password = cryptocode.decrypt(cypher_password, magic)

    info = dict()
    info['magic'] = magic
    doc_info = DOC_INFO()
    lte_info = LTE_INFO()
    camera_info = CAMERA_INFO(camera_username, camera_password)
    doc_info.gather_all(info)
    lte_info.gather_all(info)
    camera_info.gather_all(info)

    if host is None:
        return info

    host = f"{host}/field/register"
    r = requests.post(host, json=info)
    try:
        response_json = json.loads(r.text)
        return response_json
    except:
        return dict()


