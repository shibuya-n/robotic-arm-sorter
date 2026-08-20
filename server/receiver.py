"""Desktop receiver for iPhone camera frames.

The receiver intentionally does not do image recognition yet. It accepts JPEG
frames from the iOS app and stores the latest frame so recognition code can be
plugged in later.
"""

from __future__ import annotations

import argparse
import json
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Lock
from typing import Any
from urllib.parse import urlparse


MAX_FRAME_BYTES = 8 * 1024 * 1024
RUNTIME_DIR = Path(__file__).resolve().parent / "runtime"
LATEST_FRAME_PATH = RUNTIME_DIR / "latest_frame.jpg"
METADATA_PATH = RUNTIME_DIR / "latest_metadata.json"


class ReceiverState:
    def __init__(self) -> None:
        self.lock = Lock()
        self.started_at = time.time()
        self.frames_received = 0
        self.latest_metadata: dict[str, Any] | None = None

    def save_frame(self, frame_bytes: bytes, headers: dict[str, str]) -> dict[str, Any]:
        RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
        received_at = time.time()

        # Recognition code can be called from this function later.
        recognition_result = process_frame(frame_bytes, headers)

        with self.lock:
            self.frames_received += 1
            frame_id = self.frames_received
            LATEST_FRAME_PATH.write_bytes(frame_bytes)

            metadata = {
                "frame_id": frame_id,
                "received_at": received_at,
                "bytes": len(frame_bytes),
                "width": headers.get("x-frame-width"),
                "height": headers.get("x-frame-height"),
                "timestamp": headers.get("x-frame-timestamp"),
                "device_id": headers.get("x-device-id"),
                "recognition": recognition_result,
            }
            self.latest_metadata = metadata
            METADATA_PATH.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
            return metadata

    def health(self) -> dict[str, Any]:
        with self.lock:
            latest = self.latest_metadata
            return {
                "status": "ok",
                "frames_received": self.frames_received,
                "latest_frame_at": latest["received_at"] if latest else None,
                "uptime_seconds": round(time.time() - self.started_at, 2),
            }


def process_frame(frame_bytes: bytes, headers: dict[str, str]) -> dict[str, Any] | None:
    """Future hook for image recognition.

    Replace this function, or call your friend's recognition pipeline from here.
    Return JSON-serializable data if recognition results should be sent back.
    """

    _ = frame_bytes
    _ = headers
    return None


class CameraFrameHandler(BaseHTTPRequestHandler):
    state = ReceiverState()

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/":
            self.send_html(index_html())
        elif path == "/health":
            self.send_json(self.state.health())
        elif path == "/metadata":
            self.send_json(self.state.latest_metadata or {"status": "waiting_for_frames"})
        elif path == "/latest.jpg":
            self.send_latest_frame()
        else:
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path != "/frame":
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")
            return

        content_length = self.headers.get("Content-Length")
        if content_length is None:
            self.send_error(HTTPStatus.LENGTH_REQUIRED, "Content-Length is required")
            return

        try:
            byte_count = int(content_length)
        except ValueError:
            self.send_error(HTTPStatus.BAD_REQUEST, "Invalid Content-Length")
            return

        if byte_count <= 0:
            self.send_error(HTTPStatus.BAD_REQUEST, "Frame body is empty")
            return
        if byte_count > MAX_FRAME_BYTES:
            self.send_error(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, "Frame is too large")
            return

        frame_bytes = self.rfile.read(byte_count)
        if not looks_like_jpeg(frame_bytes):
            self.send_error(HTTPStatus.UNSUPPORTED_MEDIA_TYPE, "Expected image/jpeg data")
            return

        headers = {key.lower(): value for key, value in self.headers.items()}
        metadata = self.state.save_frame(frame_bytes, headers)
        self.send_json({"status": "received", **metadata})

    def send_latest_frame(self) -> None:
        if not LATEST_FRAME_PATH.exists():
            self.send_error(HTTPStatus.NOT_FOUND, "No frame has been received yet")
            return

        frame = LATEST_FRAME_PATH.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "image/jpeg")
        self.send_header("Content-Length", str(len(frame)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(frame)

    def send_json(self, payload: dict[str, Any]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def send_html(self, html: str) -> None:
        body = html.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: Any) -> None:
        print(f"{self.client_address[0]} - {format % args}")


def looks_like_jpeg(data: bytes) -> bool:
    return len(data) >= 4 and data[:2] == b"\xff\xd8" and data[-2:] == b"\xff\xd9"


def index_html() -> str:
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Robot Camera Receiver</title>
  <style>
    body {
      margin: 0;
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: #101418;
      color: #f3f6f8;
    }
    main {
      max-width: 920px;
      margin: 0 auto;
      padding: 24px;
    }
    h1 {
      margin: 0 0 16px;
      font-size: 28px;
    }
    img {
      width: 100%;
      min-height: 320px;
      object-fit: contain;
      background: #050607;
      border: 1px solid #27313a;
    }
    pre {
      padding: 12px;
      overflow: auto;
      background: #182026;
      border: 1px solid #27313a;
    }
  </style>
</head>
<body>
  <main>
    <h1>Robot Camera Receiver</h1>
    <img id="frame" alt="Waiting for frames">
    <pre id="metadata">Waiting for frames...</pre>
  </main>
  <script>
    async function refresh() {
      document.getElementById("frame").src = "/latest.jpg?t=" + Date.now();
      try {
        const response = await fetch("/metadata", { cache: "no-store" });
        const metadata = await response.json();
        document.getElementById("metadata").textContent = JSON.stringify(metadata, null, 2);
      } catch (error) {
        document.getElementById("metadata").textContent = String(error);
      }
    }
    refresh();
    setInterval(refresh, 500);
  </script>
</body>
</html>"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Receive iPhone camera frames over HTTP.")
    parser.add_argument("--host", default="0.0.0.0", help="Host interface to bind.")
    parser.add_argument("--port", type=int, default=8765, help="Port to listen on.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    server = ThreadingHTTPServer((args.host, args.port), CameraFrameHandler)
    print(f"Receiver running at http://{args.host}:{args.port}")
    print("Open http://localhost:%s to view the latest frame." % args.port)
    server.serve_forever()


if __name__ == "__main__":
    main()
