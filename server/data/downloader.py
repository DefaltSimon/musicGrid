# coding=utf-8
import asyncio
import os
import configparser
import time
import pafy
from yaml import load, dump
from mutagen.mp4 import MP4

from .utils import parse_title, clean, TagRefs, verify_filename, make_extension, is_empty


parser = configparser.ConfigParser()
parser.read("data/config.ini")

MUSIC_PATH = parser.get("downloads", "music-folder")

if not os.path.isdir(MUSIC_PATH):
    os.mkdir(MUSIC_PATH)

if not str(MUSIC_PATH).endswith(("/", "\\", "\\\\")):
    MUSIC_PATH += os.path.sep


class DataHandler:
    def __init__(self, file, loop=asyncio.get_event_loop()):
        self.filename = str(file)

        # Loads the file into memory
        if os.path.isfile(self.filename) and not is_empty(self.filename):
            with open(self.filename, "r") as fl:
                self.cached = load(fl.read())
        else:
            self.cached = {}

        self.loop = loop

        # Used for thread-safe file writing
        self.thread_lock = False

    # Used to queue the file writes
    def lock(self):
        self.thread_lock = True

    def wait_until_release(self):
        while self.thread_lock is True:
            time.sleep(0.005)

    def release_lock(self):
        self.thread_lock = False

    def write_changes(self):
        self.wait_until_release()
        self.lock()

        with open(self.filename, "w") as file:
            file.write(dump(self.cached, default_flow_style=False))

        self.release_lock()


class IdHandler(DataHandler):
    def __init__(self, loop=asyncio.get_event_loop()):
        self.file = "data/cache.yml"

        super().__init__(self.file, loop)

        self.check_cache()

    def add_new_entry(self, yt_id, filename):
        self.cached[str(yt_id)] = {
            "path": filename,
            "timestamp": time.time()
        }

        self.write_changes()

    def does_exist(self, yt_id):
        return yt_id in self.cached.keys()

    def get_path(self, yt_id):
        return self.cached.get(yt_id).get("path")

    def check_cache(self):
        for ytid, val in list(self.cached.items()):
            if not os.path.isfile(val.get("path")):
                del self.cached[ytid]

        self.write_changes()


class AudioDownloader:
    def __init__(self, api_key=None):
        if api_key:
            pafy.set_api_key(api_key)

        if not os.path.isdir(MUSIC_PATH):
            os.mkdir(MUSIC_PATH)

        self.loop = asyncio.get_event_loop()
        self.fh = IdHandler(self.loop)

    def request_music(self, url):
        if self.fh.does_exist(url):
            print("[*] {} found in cache".format(url))
            return self.fh.get_path(url)

        else:
            path = self.get_audio(url)
            self.fh.add_new_entry(url, path)

            return path

    def get_audio(self, url):
        try:
            pf = pafy.new(url, basic=True)
        except OSError:
            # Raised when the video does not exist
            return None

        title = pf.title
        audio = pf.getbestaudio(preftype="m4a")

        artist, title = parse_title(title)
        artist, title = clean(artist), clean(title)

        fn = self._download("{}-{}".format(artist, title), audio)

        mp4 = MP4(fn)
        # Reset the tags if they exist
        mp4.delete()
        mp4.add_tags()

        # Apply tags
        mp4.tags[TagRefs.TITLE] = title
        if artist is not None:
            mp4.tags[TagRefs.ARTIST] = artist
        mp4.tags[TagRefs.YEAR] = pf.published.split("-")[0]

        mp4.save()
        return fn

    @staticmethod
    def _download(title, stream):
        print("[*] Downloading {}...".format(title))

        path = MUSIC_PATH + verify_filename(title + make_extension(stream.extension))

        try:
            stream.download(path, quiet=True)
        except FileExistsError:
            os.remove(path)
            stream.download(path, quiet=True)

        return path
