import contextlib
import json
import logging
from json import JSONDecodeError
from typing import Any
from typing import Mapping

from bs4 import BeautifulSoup
from requests import Response, PreparedRequest

try:
    # Handle optional dependency
    from pygments import highlight
    from pygments.formatters.terminal import TerminalFormatter
    from pygments.lexer import RegexLexer, bygroups
    from pygments.lexers import JsonLexer, HtmlLexer, HttpLexer
    from pygments.token import Name, Text, String

    def highlight_http(content):
        return highlight(content, HttpLexer(), TerminalFormatter())

    def highlight_json(content):
        return highlight(content, JsonLexer(), TerminalFormatter())

    def highlight_html(content):
        return highlight(content, HtmlLexer(), TerminalFormatter())

except ImportError:
    # dummy highlighter
    def highlight(content: Any, *_args, **_kwargs):
        return content + "\n"

    highlight_http = highlight_json = highlight_html = highlight

__all__ = ["RequestResponseFormatter"]


IGNORE_HEADERS = [
    "Cache-Control",
    "Content-Security-Policy",
    "Cookie",
    "Set-Cookie",
    "Strict-Transport-Security",
    "X-Content-Security-Policy",
    "X-WebKit-CSP",
    "X-Content-Type-Options",
    "X-XSS-Protection",
    "X-Frame-Options",
]


class RequestResponseFormatter(logging.Formatter):
    @staticmethod
    def format_body(body: str, content_type=None):
        if not content_type:
            return "<unknown>"
        elif not body:
            return "<empty>"
        elif not isinstance(body, (str, bytes)):
            return "<binary>"

        with contextlib.suppress(AttributeError, JSONDecodeError):
            if "application/json" in content_type:
                content = json.dumps(json.loads(body), indent=2, sort_keys=True)
                return highlight_json(content)
            elif "text/html" in content_type:
                content = BeautifulSoup(body, "html.parser").prettify()
                return highlight_html(content)
        return body

    @staticmethod
    def format_headers(prefix, headers: Mapping):
        items = [prefix] + [
            f"{k}: {v}" for k, v in headers.items() if k not in IGNORE_HEADERS
        ]
        content = "\n".join(items)
        return highlight_http(content)

    def format_request(self, request: PreparedRequest):
        version = "1.1"  # default
        status = f"{request.method} {request.path_url} HTTP/{version}"
        return "\n".join(
            [
                self.format_headers(status, request.headers),
                self.format_body(request.body, request.headers.get("Content-Type"))
                + "\n",
            ]
        )

    def format_response(self, response: Response):
        if (_version := response.raw.version) == 10:
            version = "1.0"
        elif _version == 11:
            version = "1.1"
        elif _version == 20:
            version = "2.0"
        else:
            version = "unknown"
        status = f"HTTP/{version} {response.status_code} {response.reason}"
        return "\n".join(
            [
                self.format_headers(status, response.headers),
                self.format_body(response.text, response.headers.get("Content-Type")),
            ]
        )

    def format(self, record: logging.LogRecord) -> str:
        """
        Usage: LOGGER.info("Log line", extra={"request": request, "response": response})
        Will try to get request from response object (unless explicitly supplied)
        """
        response: Response = getattr(record, "response", None)
        request: PreparedRequest = getattr(
            record, "request", getattr(response, "request", None)
        )
        msg = super().format(record)
        if request:
            if msg[:-1] != "\n":
                msg = msg + "\n"
            msg = msg + self.format_request(request)
        if response is not None:
            if msg[:-1] != "\n":
                msg = msg + "\n"
            msg = msg + self.format_response(response)
        return msg
    