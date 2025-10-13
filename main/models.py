import http.client
import json
import logging
import requests
import tempfile
import uuid

from django.http import HttpResponse, JsonResponse


from django.db import models

from ast import literal_eval
import os

# Create your models here.

logging.basicConfig(level=logging.DEBUG)

host = os.getenv("HOST", "https://nextgen.visibleaccess.net" )

def parse_register_response(response):
    try:
        for item in response['cmd']:
            if item['type'] == "wireguard":
                if len(item['data']):
                    with open("/etc/wireguard/wg.xx", 'w') as f:
                        f.write(item['data'])

    except Exception as e:
        print(e)


def upload_file_to_to_s3(file, data):
    temp_path = tempfile.mkdtemp()
    temp_name = uuid.uuid4().hex
    filename = os.path.join(temp_path, temp_name)

    try:
        with open(filename, "wb+") as destination:
            if file is not None:
                for chunk in file.chunks():
                    destination.write(chunk)
            else:
                if data is not None:
                    destination.write(bytes(data, 'utf-8'))

        files = {'upload_file': open(filename, 'rb')}
        url = f"{host}/field/upload_file"
        r = requests.post(url, files=files, data={})
        info = json.loads(r.text)
        return info['files'][0]

    except:
        return None



