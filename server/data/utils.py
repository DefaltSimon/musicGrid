# coding=utf-8
import re
import socket
import os
import subprocess
import threading
from werkzeug.utils import secure_filename


class TagRefs:
    TITLE = u"\xa9nam"
    ALBUM = u"\xa9alb"
    ARTIST = u"\xa9ART"
    YEAR = u"\xa9day"
    COMMENT = u"\xa9cmt"
    DESCRIPTION = u"desc"

    ENCODED_BY = u"\xa9too"

AUDIO_EXTENSIONS = (".m4a", ".mp3", ".mp4", ".ogg", ".wav", ".aac", ".wma")

filters = [
    "[Official Video]", "(Audio)",
    "(Lyric video)", "Lyric video", "[Lyric video]",
    "(Official music video)", "[Official music video]"
    "[edm]", "[trap]", "[Proximity exclusive]", "[NCS release]",
    "[Premiere]",
]

compiled_filters = [re.compile(re.escape(comp), re.IGNORECASE) for comp in filters]


def clean(title):
    for f in compiled_filters:
        title = f.sub("", str(title))

    return str(title).strip(" ")


def replace_spaces(path):
    return str(path).replace(" ", "_")


def verify_filename(path):
    path = replace_spaces(path)
    return secure_filename(path)


def make_extension(ext):
    return "." + ext


def parse_title(title):
    if len(title.split("-")) == 2:
        ls = [str(a).strip(" ") for a in title.split("-")]
        # Can be unpacked
        return ls
    else:
        return None, title


def threaded(fn):
    def wrapper(*args, **kwargs):
        threading.Thread(target=fn, args=args, kwargs=kwargs).start()
    return wrapper


def is_empty(path):
    if os.path.isfile(path):
        return os.stat(path).st_size == 0
    else:
        return False


def find_my_ip():
    # ON LINUX:
    # WARNING: ASSUMES YOU HAVE ETH0 AS YOUR PRIMARY network card
    # CHANGE TO wlan0 if you are connected via wifi
    inet_card = "eth0"
    nxt = "lo"

    if os.name == "nt":
        return socket.gethostbyname(socket.gethostname())

    else:
        # Assumes Linux
        p_output = subprocess.check_output(["ifconfig"]).decode("utf-8")

        dc = str(p_output).split(nxt)[0]
        if dc.find(inet_card) == -1:
            raise ValueError("No {} interface found".format(inet_card))

        comp = re.compile(r"inet addr:[1-9]+\.[1-9]+\.[1-9]+\.[1-9]+", re.U)
        result = re.search(comp, dc).group(0).replace("inet addr:", "")

        return result


def correct_url(url):
    return str(url).replace(os.path.sep, "/")
