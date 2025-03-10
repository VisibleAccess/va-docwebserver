import time
import requests

while 1:
  try:
    c = requests.get("http://localhost:8000/dbupdate")
  except:
    pass
  time.sleep(5)

