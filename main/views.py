import http.client

from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse
from .speedtest_helper import start_speedtest

from .udp_db import udp_db

import requests
import json

# Create your views here.
vpn_ip = udp_db.get_value('vpn_ip')
host_dev = "https://dev.nextgen.visibleaccess.net"
host = "https://nextgen.visibleaccess.net"
def db_dump(request):
    return JsonResponse(udp_db._db)
    db_str = udp_db.db_str()
    db_str = db_str.replace('\n', '<br>')
    db_str = db_str.replace(' ', '&nbsp')
    return HttpResponse(db_str)
def db_update_request(request):
    udp_db.update()
    return HttpResponse("")

def db_test(request):
    x = udp_db.get_value_dict("LTEMONITOR:RSSI")
    try:
        return JsonResponse(x)
    except:
        return HttpResponse()

def speed_test(request):
    print("Starting speedtest")
    udp_db.remove_key(["SPEEDTEST"])
    start_speedtest(udp_db.udp_broadcast)
    return HttpResponse("OK")


def default(request):
    return render(request, 'index.html')


def udp_bcast(request):
    msg = request.GET['msg']
    udp_db.send_msg(msg)
    return HttpResponse("")


def lte_connected(request):
    try:
        r = requests.get("https://httpstat.us/200")
        if r.status_code == 200:
            return HttpResponse("OK")
    except:
        pass
    return HttpResponse(status=http.client.BAD_REQUEST)

def snapshot(request):
    try:
        add_rotation = int(request.GET.get("add_rotation", 0))
        if vpn_ip:
            url = f"{host_dev}/field/vpn_snapshot?ip=10.1.1.16&add_rotation={add_rotation}"
            r = requests.get(url, timeout=6)
            if r.status_code == 200:
                return HttpResponse(r.content, content_type="image/jpeg")
    except Exception as e:
        pass

    return HttpResponse(status=http.client.BAD_REQUEST)


def building(request):
    name = request.GET.get('name')
    address = request.GET.get('address')

    try:
        url = f"https://dev.nextgen.visibleaccess.net/field/building_info"
        r = requests.get(url, params={"name":name, "address":address, "set": 1, "ip": vpn_ip})
        print("building status", r.status_code)
        if r.status_code == 200:
            resp = json.loads(r.text)
            udp_db.save_building_info(resp['name'], resp['address'], resp['photo'])
        return HttpResponse("OK", status=r.status_code)
    except:
        return HttpResponse("ERROR", status=http.client.BAD_REQUEST)







