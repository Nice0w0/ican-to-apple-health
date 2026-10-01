"""
Vercel Python serverless entry point: POST /api/convert

Vercel discovers a `handler` subclass of BaseHTTPRequestHandler in each file
under api/ and runs it. No framework, no requirements.txt, no build step --
which is what makes the free tier enough and leaves nothing to maintain.
"""

import json
import os
import sys
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cgm import BadRequest, convert  # noqa: E402


class handler(BaseHTTPRequestHandler):
    def _send(self, status, payload, extra=None):
        body = json.dumps(payload, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        for key, value in (extra or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def _error(self, query, status, message):
        # The published shortcut asks for on_error=empty. Shortcuts does not
        # treat a 4xx/5xx as a failure: it hands the body on, Repeat with Each
        # walks the {"error": ...} dictionary, and Log Health Sample writes an
        # empty value -- a glucose of 0, stamped with the current time, which
        # only the wearer can delete by hand. An empty array logs nothing.
        # The reason still travels, in X-Error, for anyone debugging with curl.
        if query.get("on_error") == "empty":
            # Header values are latin-1; messages can quote Thai headers.
            reason = ("%d %s" % (status, message)).encode(
                "ascii", "backslashreplace").decode()
            return self._send(200, [], {"X-Error": reason})
        return self._send(status, {"error": message})

    def do_GET(self):
        self._send(200, {"ok": True})

    def do_POST(self):
        query = {k: v[0] for k, v in parse_qs(urlparse(self.path).query).items()}
        # Header form is friendlier for clients that can set headers; the query
        # form exists for those that cannot.
        if "X-Token" in self.headers:
            query.setdefault("token", self.headers["X-Token"])

        try:
            length = int(self.headers.get("Content-Length") or 0)
            body = self.rfile.read(length) if length else b""
            readings, total, unit, source_unit, cutoff = convert(
                body, self.headers.get("Content-Type", ""), query)
        except BadRequest as exc:
            return self._error(query, exc.status, exc.message)
        except Exception as exc:                    # never leak a stack trace
            return self._error(query, 500, "conversion failed: %s" % exc)

        self._send(200, readings, {
            "X-Readings-Total": str(total),
            "X-Readings-Returned": str(len(readings)),
            "X-Unit": unit,
            "X-Source-Unit": source_unit,
            # Echoed so a caller can tell "nothing new" from "the cursor never
            # arrived" -- the two look identical from an empty array.
            "X-Since": cutoff.isoformat(timespec="seconds") if cutoff else "none",
        })
