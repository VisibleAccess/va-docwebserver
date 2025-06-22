import logging

from django.db import models

from ast import literal_eval
import os

# Create your models here.

logging.basicConfig(level=logging.DEBUG)


def parse_register_response(response):
    try:
        for item in response['cmd']:
            if item['type'] == "wireguard":
                if len(item['data']):
                    with open("/etc/wireguard/wg.xx", 'w') as f:
                        f.write(item['data'])

    except Exception as e:
        print(e)




