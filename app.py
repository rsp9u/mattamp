import os
import os.path
import json
import urllib
import requests
import traceback
from http.server import HTTPServer, SimpleHTTPRequestHandler

# envs
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN")
MATTER_HOST = os.environ.get("MATTER_HOST")
LISTEN_PORT = int(os.environ.get("LISTEN_PORT"))
IMAGE_WIDTH = os.environ.get("IMAGE_WIDTH")
IMAGE_HEIGHT = os.environ.get("IMAGE_HEIGHT")
IMPERSONATE = (os.environ.get("IMPERSONATE") == "true")
LIST_FILE_DIR = os.environ.get("LIST_FILE_DIR", ".")

# constants
PUBLINK_LIST = os.path.join(LIST_FILE_DIR, "publink.list")
TOKEN_LIST = os.path.join(LIST_FILE_DIR, "token.list")
AUTH_HEADER = {"Authorization": "Bearer {}".format(ADMIN_TOKEN)}
MATTER_API = "{}/api/v4".format(MATTER_HOST)
IMAGE_SIZE = "={}x{}".format(IMAGE_WIDTH, IMAGE_HEIGHT)


class KeyValueFile:
    def __init__(self, path):
        self.path = path

    def write(self, k, v):
        try:
            with open(self.path, "r") as f:
                d = json.load(f)
        except FileNotFoundError:
            d = {}

        d[k] = v

        with open(self.path, "w") as f:
            json.dump(d, f, indent=2)

    def read(self, k):
        try:
            with open(self.path, "r") as f:
                return json.load(f).get(k)
        except FileNotFoundError:
            return None


publink_file = KeyValueFile(PUBLINK_LIST)
token_file = KeyValueFile(TOKEN_LIST)


def upload_emoji(emoji_name, channel_id):
    print("=== upload_emoji ===")
    emojis = requests.get("{}/emoji".format(MATTER_API), headers=AUTH_HEADER).json()

    emoji = [e for e in emojis if e["name"] == emoji_name]
    if len(emoji) != 1:
        print("error: not found emoji {}".format(emoji_name))
        return None

    img_resp = requests.get("{}/emoji/{}/image".format(MATTER_API, emoji[0]["id"]), headers=AUTH_HEADER)
    if not img_resp.ok:
        print("error: failed to get emoji image; {}".format(img_resp.text))
        return None

    headers = {'Content-Type': 'application/octet-stream'}
    headers.update(AUTH_HEADER)
    up_resp = requests.post("{}/files".format(MATTER_API),
                            headers=headers,
                            params={
                                "filename": emoji_name + ".png",
                                "channel_id": "6pf6wed9qbnxfq6rwoa6qqjguw"
                            },
                            data=img_resp.content)
    if not up_resp.ok:
        print("error: failed to upload emoji image; {}".format(up_resp.text))
        return None

    print(up_resp.json())
    return up_resp.json()["file_infos"][0]["id"]


def create_access_token(user_id):
    print("=== create_access_token ===")
    body = {"description": "matamp"}
    resp = requests.post("{}/users/{}/tokens".format(MATTER_API, user_id), headers=AUTH_HEADER, json=body)
    if not resp.ok:
        print("error: failed to craete access token; {}".format(resp.text))
        return None

    print(json.dumps(resp.json(), indent=2))
    token = resp.json()["token"]
    token_file.write(user_id, token)
    return token


class RequestHandler(SimpleHTTPRequestHandler, object):
    def parse_urlform(self, s):
        d = {}
        for kv in s.split('&'):
            k, v = kv.split('=')
            d[urllib.parse.unquote(k)] = urllib.parse.unquote(v)
        return d

    def do_POST(self):
        try:
            print("{} {}".format(self.command, self.path))
            print(self.headers)
            self._do_POST()

        except Exception:
            print("error: unknown exception")
            print(traceback.format_exc())

    def _do_POST(self):
        content_len = int(self.headers.get('Content-Length'))
        req_body_byte = self.rfile.read(content_len)
        req_body = req_body_byte.decode('utf-8')
        req_data = self.parse_urlform(req_body)
        print("==== Request ====")
        print(json.dumps(req_data, indent=2))

        channel_id = req_data["channel_id"]
        user_id = req_data["user_id"]
        emoji_name = req_data["text"].strip(":")

        public_link = publink_file.read(emoji_name)
        if public_link is None:
            self._post_with_img_attachment(emoji_name, channel_id)
        else:
            self._post_with_img_link(channel_id, user_id, public_link)

    def _post_with_img_attachment(self, emoji_name, channel_id):
        file_id = upload_emoji(emoji_name, channel_id)
        if file_id is None:
            print("error: file upload error")
            return

        body = {
            "channel_id": channel_id,
            "message": "",
            "file_ids": [file_id],
        }
        resp = requests.post("{}/posts".format(MATTER_API), headers=AUTH_HEADER, json=body)
        print("==== Posts ====")
        print(json.dumps(resp.json(), indent=2))

        resp = requests.get("{}/files/{}/link".format(MATTER_API, file_id), headers=AUTH_HEADER)
        print("==== Public link ====")
        print(json.dumps(resp.json(), indent=2))
        public_link = resp.json()["link"]
        publink_file.write(emoji_name, public_link)
        self.send_response(200)
        self.end_headers()

    def _post_with_img_link(self, channel_id, user_id, public_link):
        msg = "![]({} {})".format(public_link, IMAGE_SIZE)

        if IMPERSONATE:
            token = token_file.read(user_id)
            if token is None:
                token = create_access_token(user_id)
            headers = {"Authorization": "Bearer {}".format(token)}

            body = {"channel_id": channel_id, "message": msg}
            resp = requests.post("{}/posts".format(MATTER_API), headers=headers, json=body)
            print("==== Posts ====")
            print(json.dumps(resp.json(), indent=2))
            self.send_response(200)
            self.end_headers()

        else:
            data = {"text": msg, "response_type": "in_channel"}
            print("==== Response ====")
            print(json.dumps(data, indent=2))
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(data).encode())


httpd = HTTPServer(("", LISTEN_PORT), RequestHandler)
httpd.serve_forever()
