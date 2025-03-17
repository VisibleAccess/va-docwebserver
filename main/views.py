import http.client

from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse
from .speedtest_helper import start_speedtest

from .udp_db import udp_db

import requests

# Create your views here.


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
    print(request)
    return render(request, 'index.html')


def udp_bcast(request):
    msg = request.GET['msg']
    udp_db.send_msg(msg)
    return HttpResponse("")


def lte_connected(request):
    r = requests.get("https://httpstat.us/200")
    if r.status_code == 200:
        return HttpResponse("OK")
    return HttpResponse(status=http.client.BAD_REQUEST)
