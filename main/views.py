import http.client

from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse
from .speedtest_helper import start_speedtest
from .register import register_device

from .udp_db import udp_db
from .models import parse_register_response

import os
import requests
import json
import random

# Create your views here.
vpn_ip = udp_db.get_value('vpn_ip')
host = os.getenv("HOST", "https://nextgen.visibleaccess.net" )




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
    return render(request, 'index.html', {'script_version': str(random.random())})


def udp_bcast(request):
    msg = request.GET['msg']
    udp_db.send_msg(msg)
    return HttpResponse("")


def lte_connected(request):
    try:
        default_url = f"{host}/field/lte_status"
        lte_timeout = int(os.getenv("LTE_CONNECT_TIMEOUT", 6))
        url = os.getenv("LTE_CONNECT_STATUS_URL", default_url)
        r = requests.get(url, timeout=lte_timeout)
        if r.status_code == 200:
            return HttpResponse("OK")
    except:
        pass
    return HttpResponse(status=http.client.BAD_REQUEST)

def snapshot(request):
    try:
        add_rotation = int(request.GET.get("add_rotation", 0))
        if vpn_ip:
            url = f"{host}/field/vpn_snapshot?ip={vpn_ip}&add_rotation={add_rotation}"
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
        url = f"{host}/field/building_info"
        r = requests.get(url, params={"name":name, "address":address, "set": 1, "ip": vpn_ip})
        print("building status", r.status_code)
        if r.status_code == 200:
            resp = json.loads(r.text)
            udp_db.save_building_info(resp['name'], resp['address'], photo=resp['photo'])
        return HttpResponse("OK", status=r.status_code)
    except:
        return HttpResponse("ERROR", status=http.client.BAD_REQUEST)



def register(request):
    magic = request.GET.get('magic', "foobar")
    #response = register_device(host, magic)
    response = register_device("https://staging.nextgen.visibleaccess.net", magic)
    parse_register_response(response)
    return JsonResponse(response)




