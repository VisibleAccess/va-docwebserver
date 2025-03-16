import speedtest
from threading import Thread
import os
import requests
import time
from .udp_broadcast import UDPBroadcastController

def speedtest_thread(udp_broadcast):
    try:
        st = speedtest.Speedtest(secure=True)
        print("Get servers")
        st.get_servers()
        st.get_best_server()
        print("download")
        st.download()
        print("upload")
        st.upload()

        results = st.results.dict()
        results['serial_number'] = os.environ.get("SERIAL_NUMBER", "???")
        results['building_name'] = os.environ.get("BUILDING_NAME", "???")
        requests.post("https://dev.nextgen.visibleaccess.net/field/splunk_log?msg=SPEEDTEST", json=results)
        print(results)

        if udp_broadcast:
            udp_broadcast.udp_tx_broadcast(f"TIME:{int(time.time())}", module_name="SPEEDTEST")
            udp_broadcast.udp_tx_broadcast(f"ZING:{int(results['ping'])}", module_name="SPEEDTEST")
            udp_broadcast.udp_tx_broadcast(f"UPLOAD:{int(results['upload']/10000)/100}", module_name="SPEEDTEST")
            udp_broadcast.udp_tx_broadcast(f"DOWNLOAD:{int(results['download']/10000)/100}", module_name="SPEEDTEST")
            udp_broadcast.udp_tx_broadcast(f"LOCATION:{results['server']['name']}", module_name="SPEEDTEST")
            udp_broadcast.udp_tx_broadcast(f"IPADDR:{results['client']['ip']}", module_name="SPEEDTEST")
    except Exception as e:
        print("error", e)



def start_speedtest(udp_broadcast=None):
    thread = Thread(target=speedtest_thread, args=(udp_broadcast,))
    thread.start()

if __name__ == "__main__":
    udp_controller = UDPBroadcastController(module_name="SPEEDTEST", interfaces=["en0"], port=1120)
    start_speedtest(udp_controller)

