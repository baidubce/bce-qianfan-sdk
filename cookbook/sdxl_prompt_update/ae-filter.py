import csv
import argparse
import http.server
import json
import shutil
from typing import Any
from urllib.parse import urlparse, parse_qsl
from pathlib import Path, PurePath
import os

"""
filter results by their AE score
- get the score from the CSV (so we on'y need to scan once)
- scan and get the results, 
  - then filter and delete?
  - filter into a new directory?
"""


class AEHTTPHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, request, client_address, server):
        super().__init__(request, client_address, server)

    def do_GET(self):
        self.protocol_version = "HTTP/1.1"

        path = urlparse(self.path)
        if path.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            with open("index.html", "r") as f:
                self.wfile.write(f.read().encode("utf-8"))
        elif path.path.endswith(".css"):
            self.send_response(200)
            self.send_header("Content-type", "text/css")
            self.end_headers()
            with open("main.css", "r") as f:
                self.wfile.write(f.read().encode("utf-8"))
        elif path.path.endswith(".png"):
            self.send_response(200)
            self.send_header("Content-type", "image/png")
            self.end_headers()

            dir_path = PurePath(
                self.server.state["dir"],
            )
            with open(
                os.path.join(dir_path, self.path[5:]),
                "rb",
            ) as f:
                self.wfile.write(f.read())
        elif path.path.endswith(".jpg"):
            self.send_response(200)
            self.send_header("Content-type", "image/jpeg")
            self.end_headers()

            dir_path = PurePath(
                self.server.state["dir"],
            )
            with open(
                os.path.join(dir_path, self.path[5:]),
                "rb",
            ) as f:
                self.wfile.write(f.read())
        elif path.path.endswith(".webp"):
            self.send_response(200)
            self.send_header("Content-type", "image/webp")
            self.end_headers()

            dir_path = PurePath(
                self.server.state["dir"],
            )
            with open(
                os.path.join(dir_path, self.path[5:]),
                "rb",
            ) as f:
                self.wfile.write(f.read())
        elif path.path.endswith(".jpeg"):
            self.send_response(200)
            self.send_header("Content-type", "image/jpeg")
            self.end_headers()

            dir_path = PurePath(
                self.server.state["dir"],
            )
            with open(
                os.path.join(dir_path, self.path[5:]),
                "rb",
            ) as f:
                self.wfile.write(f.read())
        elif path.path.endswith(".js"):
            self.send_response(200)
            self.send_header("Content-type", "text/javascript")
            self.end_headers()
            with open(self.path[1:], "r") as f:
                self.wfile.write(f.read().encode("utf-8"))
        elif path.path[1:7] == "filter" and path.path.endswith(".json"):
            from collections import ChainMap

            # params = ChainMap(parse_qsl(path.query))
            params = {}
            [params.update({k: v}) for (k, v) in parse_qsl(path.query)]

            out = filter_by_score_range(
                self.server.state["results"], float(params["min"]), float(params["max"])
            )
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(out).encode("utf-8"))

        else:
            self.send_header("Content-type", "application/json")
            self.send_response(404)
            self.end_headers()
            out = json.dumps({"hello": "world"}).encode("utf-8")
            self.wfile.write(out)


def get_info(file):
    results = []

    with open(file) as f:
        reader = csv.reader(f)

        for i, row in enumerate(reader):
            # skip header row
            if i == 0:
                continue

            results.append({"file": row[0], "score": float(row[1])})

    return results


def by_score(min, max):
    return lambda result: result["score"] >= min and result["score"] <= max


def filter_by_score_range(results, min, max):
    return [x for x in filter(by_score(min, max), results)]
    # return [item for item in results if by_score(min, max)(item)]


class AEHTTPServer(http.server.ThreadingHTTPServer):
    def __init__(
        self, state, server_address, request_handler_class, bind_and_activate=True
    ):
        self.state = state
        super().__init__(server_address, request_handler_class, bind_and_activate)


def server(args, results):
    server_address = ("localhost", args.port)
    httpd = AEHTTPServer(results, server_address, AEHTTPHandler)
    print(
        f"Server running on http://{httpd.server_address[0]}:{httpd.server_address[1]}"
    )

    httpd.state = {"results": results, "dir": args.images_dir}
    httpd.serve_forever()


def main(args):
    results = get_info(args.scores_file)

    if args.server:
        server(args, results)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("scores_file", help="Scores CSV file to filter your results")
    parser.add_argument(
        "--images_dir",
        required=True,
        help="Directory where the images are located for this CSV file for loading the images into the website",
    )
    parser.add_argument(
        "--server",
        default=False,
        action="store_true",
        help="Run a webserver to view filtering in your browser.",
    )
    parser.add_argument(
        "--port", default=3456, type=int, help="Set the port to run the server on."
    )
    args = parser.parse_args()
    main(args)
