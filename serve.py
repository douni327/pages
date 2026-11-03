#!/usr/bin/env python3
"""
receipt.html 페이지와 GetPayResult API를 '같은 출처'로 제공하는 임시 서버.

- /                  -> receipt.html (같은 폴더)
- /api/...           -> http://quick.kimsoft.kr:15013/... 로 프록시
같은 출처이므로 브라우저의 CORS / 혼합콘텐츠(https->http) 문제가 없습니다.

사내망(= quick.kimsoft.kr 에 접속 가능한) PC/서버에서 실행하세요:
    python3 serve.py            # 기본 0.0.0.0:8080
    python3 serve.py 9000       # 포트 지정

외부 임시 공개가 필요하면 터널을 붙이세요(둘 중 하나):
    cloudflared tunnel --url http://localhost:8080
    ngrok http 8080

이때 receipt.html 의 'API 주소' 칸을 아래로 바꾸면 됩니다:
    /api/Quickiyo/Iamport/CreditCard/GetPayResult?sOrderKey=
"""
import sys
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

UPSTREAM = "http://quick.kimsoft.kr:15013"
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8080


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/api/"):
            self._proxy(self.path[len("/api"):])
        elif self.path in ("/", "/receipt.html", "/index.html"):
            self._serve_file("receipt.html")
        else:
            self.send_error(404)

    def _serve_file(self, name):
        try:
            with open(name, "rb") as f:
                body = f.read()
        except OSError:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _proxy(self, upstream_path):
        url = UPSTREAM + upstream_path
        try:
            with urllib.request.urlopen(url, timeout=30) as resp:
                body = resp.read()
                ctype = resp.headers.get("Content-Type", "application/json; charset=utf-8")
                status = resp.status
        except urllib.error.HTTPError as e:
            body, ctype, status = e.read(), "application/json; charset=utf-8", e.code
        except Exception as e:
            msg = ('{"error":"%s"}' % str(e)).encode("utf-8")
            body, ctype, status = msg, "application/json; charset=utf-8", 502
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass  # 조용히


if __name__ == "__main__":
    print(f"Serving on http://0.0.0.0:{PORT}  (upstream: {UPSTREAM})")
    print("페이지의 'API 주소' 칸: /api/Quickiyo/Iamport/CreditCard/GetPayResult?sOrderKey=")
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
