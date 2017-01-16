# coding=utf-8
import flask
import sqlite3
import configparser
import time
import os
from OpenSSL import SSL

from data.downloader import AudioDownloader
from data.utils import AUDIO_EXTENSIONS, find_my_ip, threaded, correct_url
from data.dbmanager import DatabaseManager

__author__ = "DefaltSimon"
__version__ = "0.1"
__license__ = "MIT"


parser = configparser.ConfigParser()
parser.read("data/config.ini")

RL_INTERVAL = parser.getint("rate-limiting", "interval")
RL_AMOUNT_PER_INTERVAL = parser.getint("rate-limiting", "amount_per_interval")

MUSIC_FOLDER = parser.get("downloads", "music-folder")

DEFAULT_PORT = 80


class CredentialManager(DatabaseManager):
    def __init__(self):
        super().__init__()

    def apply_auth(self, key):
        if not self.key_exists(key):
            flask.abort(401)

        else:
            print("{} logged in with key:{}".format(flask.request.remote_addr, key))


class RateLimitManager:
    def __init__(self, rate_interval=RL_INTERVAL, limit=RL_AMOUNT_PER_INTERVAL):
        self.ips = {}
        self.history = []

        self.rate_interval = rate_interval
        self.limit = limit

        self.running = True

        # Begin checking the age of ip entries
        self.start_monitoring()

    def new_connection(self, ip):
        if not self.ips.get(ip):
            if ip not in self.history:
                self.history.append(ip)
            self.ips[ip] = [time.time()]

        else:
            self.ips[ip].append(time.time())

    @staticmethod
    def tick(last):
        ct = time.time()
        delta = abs(1 - (ct - last))
        time.sleep(delta)

        return time.time()

    @threaded
    def start_monitoring(self):
        t = time.time()

        while self.running:
            t = self.tick(t)

            for ip, ts in self.ips.items():
                for times in sorted(ts):
                    if (t - times) > self.rate_interval:
                        self.ips[ip].remove(times)

    def must_filter(self, ip):
        if not self.ips.get(ip):
            return None

        return len(self.ips[ip]) > 10

    def apply_ratelimit(self):
        ip = flask.request.remote_addr
        if self.must_filter(ip):
            # If you really decide to ddos this app, you wont know where the page went ;)
            flask.abort(404)

        self.new_connection(ip)


# The core of the musicGrid

app = flask.Flask(__name__)
audio = AudioDownloader()

rate_download = RateLimitManager()
rate_request = RateLimitManager()
rate_version = RateLimitManager()

auth = CredentialManager()


@app.route("/api/v1/music/<path:path>")
def file_serve(path):
    rate_download.apply_ratelimit()

    if not str(path).endswith(AUDIO_EXTENSIONS):
        flask.abort(404)

    return flask.send_from_directory(MUSIC_FOLDER, path)


@app.errorhandler(400)
def wrong_request(_):
    payload = {
        "success": False,
        "reason": "The request you POSTed did not have JSON data."}

    return flask.make_response(flask.jsonify(payload), 400)


@app.errorhandler(401)
def no_auth(_):
    payload = {
        "success": False,
        "reason": "Unauthorized"}

    return flask.make_response(flask.jsonify(payload), 401)


@app.errorhandler(404)
def error_handler(_):
    payload = {
        "success": False,
        "reason": "Not found"}

    return flask.make_response(flask.jsonify(payload), 404)


@app.errorhandler(405)
def method_not_allowed(_):
    payload = {
        "success": False,
        "reason": "This HTTP method is not allowed."}
    return flask.make_response(flask.jsonify(payload), 405)


@app.errorhandler(429)
def rate_limiting(_):
    payload = {
        "success": False,
        "reason": "You are being rate limited",
        "rate_limit": {
            "interval": "{} seconds".format(RL_INTERVAL),
            "amount": "{} requests".format(RL_AMOUNT_PER_INTERVAL),
        }
    }
    return flask.make_response(flask.jsonify(payload), 429)


@app.route("/api/version")
def version_getter():
    rate_version.apply_ratelimit()

    payload = {
        "version": __version__}
    return flask.jsonify(payload)


# Main Music feature
def serve_music():
    rate_request.apply_ratelimit()

    json = flask.request.get_json()

    if not json:
        flask.abort(400)

    api_key = json.get("key")
    url = json.get("video_id")
    auth.apply_auth(api_key)

    print("[*] Processing video: {}".format(url))

    filename = audio.request_music(url)

    if filename:

        in_cache = bool(audio.fh.does_exist(url))
        path = flask.request.url_root + "api/v1/" + correct_url(filename)
        extension = "." + filename.split(".")[-1]

        payload = {
            "success": True,
            "extension": extension,
            "type": "audio",
            "was-cached": in_cache,
            "download": path}

    else:
        payload = {
            "success": False,
            "reason": "The video could not be found."
        }

    return flask.jsonify(payload)


@app.route("/api/v1/get_music", methods=["GET", "POST"])
def music_route():
    # Raise 405 Method Not Allowed for GET requests
    if flask.request.method == "GET":
        flask.abort(405)

    return serve_music()


def main():
    local_ip = parser.get("networking", "ip_address") if parser.has_option("networking", "ip_address") else find_my_ip()
    port = parser.getint("networking", "port") if parser.has_option("networking", "port") else DEFAULT_PORT

    ssl = bool(os.path.isfile("certificate.crt") and os.path.isfile("priv.key"))
    ssl_cont = ("certificate.crt", "priv.key")

    if ssl:
        print("Info: HTTPS connections allowed")

    app.run(host=local_ip, port=port, debug=True, ssl_context=ssl_cont if ssl else None)


if __name__ == '__main__':
    main()
