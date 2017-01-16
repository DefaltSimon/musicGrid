# coding=utf-8
import time
import requests
from json import loads

# Set the url of the REST server
BASE_URL = "http://192.168.99.1"

MUSIC_ENDPOINT = "/api/v1/get_music"

# Get your api key with generatekey.py
api_key = "f8b6ba2baa37691311695b08b03cc430923ed1eb8dcc05f74f24f731808f33f4f5fe38ed05c20cb3b713c0d603e61c13066c078e7540817ad30bf220475255b7"
# api_key = "06ff537e115fa6a97bb5765b637894e25275df1692ebdb7a19bbb36a6c5e52ba9eeeaa6e5d3e47e6257c910dd84f0246981bfde3ad77fbff2b14596db6f6567d"


def request_music(url):
    payload = {
        "key": api_key,
        "video_id": url,
    }

    resp = requests.post(BASE_URL + MUSIC_ENDPOINT, json=payload)
    data = loads(bytes(resp.content).decode("utf-8"))

    if resp.status_code != 200:
        print("Response was " + str(resp.status_code))
        print("Got: {}".format(data))

    else:
        print("Response OK")
        print("Success: {}".format(data.get("success")))

        if data.get("success"):
            print("Audio ({}): {}".format(data.get("extension"), data.get("download")))
        else:
            print("Something went wrong: {}".format(data.get("reason")))

    print("-----------------")


# testing_vids = ["EXfLirBwBKY", "Y2V6yjjPbX0", "HwtljkGZJnI"]

while True:
    ytid = input(">")

    before = time.time()
    request_music(ytid)
    delta = time.time() - before

    print("Took {} seconds".format(delta))
