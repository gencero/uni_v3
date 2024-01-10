import requests
import json

from requests.models import HTTPError

#TARGET_URL = "https://httpbin.org/anything"

#TARGET_URL = "http://18.198.16.101:3001/uniswap/v3"
TARGET_URL = "http://localhost:3001/uniswap/v3"

HEADER = {"Authorization": "Basic YXBpdXNlcjpTMjAyMVRlcCFfenp0"}

def post_data(data):
    r = requests.post(
        TARGET_URL,
        json=data,
        headers=HEADER)
    #print("Status code:", r.status_code)
    #print(r.json())
    if r.status_code != 200:
        print("Price API error:", r.json())
        raise(HTTPError)