"""Interactive OAuth bridge for the official agy executable.

Keep the exact originating CLI process alive while the user authorizes in a
browser or pastes its code. Do not exchange tokens ourselves, read keychains,
change client IDs, export secrets or fake SSH variables. Browser completion is
NOT authentication success. Success requires a terminal SUCCESS result and, if
OAuth occurred, a second fresh-process credential reuse check.
"""
from __future__ import annotations

import platform
import re
import threading
import time
from pathlib import Path
from urllib.parse import urlparse

from .cli_runtime import runtime_env
from .cli_transport import ManagedProcess, strip_ansi, safe_diagnostic, AUTH_PROMPT

CODE_PROMPT = re.compile(r"(?:paste|enter|input)[^\n]{0,100}(?:authorization|authentication|verification|auth)[ -]?code|(?:authorization|verification) code[^\n]{0,40}:|(?:paste|enter) (?:the |your )?code(?: here)?[: ]", re.I)
SETUP_PROMPT = re.compile(r"select (?:a |your )?(?:color|colour) (?:scheme|theme)|trust this (?:folder|workspace|directory)|workspace trust", re.I)
AUTH_HOSTS = {"accounts.google.com", "antigravity.google", "www.antigravity.google", "auth.google.com"}

STAGES = {
    "STARTING": "\u6b63\u5728\u542f\u52a8 AGY \u8fde\u63a5",
    "WAITING_BROWSER": "\u8bf7\u5728\u6d4f\u89c8\u5668\u5b8c\u6210 Google \u6388\u6743",
    "WAITING_CODE": "\u8bf7\u7c98\u8d34\u672c\u6b21\u7f51\u9875\u8fd4\u56de\u7684\u6388\u6743\u7801",
    "VERIFYING": "\u6b63\u5728\u9a8c\u8bc1 AGY \u8fde\u63a5",
    "VERIFYING_REUSE": "\u6b63\u5728\u68c0\u67e5\u767b\u5f55\u51ed\u636e\u80fd\u5426\u88ab\u65b0\u4efb\u52a1\u590d\u7528",
    "SUCCESS": "AGY \u8fde\u63a5\u5df2\u9a8c\u8bc1",
    "ERROR": "AGY \u8fde\u63a5\u672a\u5b8c\u6210",
    "CANCELED": "\u5df2\u53d6\u6d88\u672c\u6b21\u8fde\u63a5",
    "TERMINAL_REQUIRED": "\u8bf7\u5148\u5728\u7cfb\u7edf\u7ec8\u7aef\u5b8c\u6210 AGY \u521d\u59cb\u5316",
}


def official_auth_url(text, *, complete_only=False):
    text = strip_ansi(text)
    for match in re.finditer(r"https://[^\s<>\"\x1b]+", text):
        if complete_only and match.end() == len(text):
            continue  # URL may be split across subprocess output chunks.
        value = match.group()
        value = value.rstrip("').,]")
        try:
            parts = urlparse(value)
            if parts.hostname in AUTH_HOSTS and not parts.username and not parts.password:
                return value
        except ValueError:
            pass
    return ""


class AuthSession:
    def __init__(self, cli, *, cwd, version="", timeout=600, model="", allow_interactive=True, process_factory=ManagedProcess):
        self.cli = cli
        self.cwd = str(cwd)
        self.version = version
        self.model = model.strip()
        self.allow_interactive = allow_interactive
        self.timeout = max(30, int(timeout))
        self._factory = process_factory
        self._mutex = threading.RLock()
        self._cancel = threading.Event()
        self._process = None
        self._url = ""
        self._stage = "STARTING"
        self._detail = ""
        self._submitted = []  # memory only, used to redact echoed input, cleared on exit
        self._auth_seen = False
        self._tools = None
        self._started = time.monotonic()

    def snapshot(self):
        with self._mutex:
            return {"stage": self._stage, "message": STAGES[self._stage],
                    "detail": self._detail, "has_url": bool(self._url),
                    "elapsed_seconds": int(time.monotonic() - self._started),
                    "image_tool_available": self._tools}

    def browser_url(self):
        with self._mutex:
            return self._url

    def _set(self, stage, detail=""):
        with self._mutex:
            self._stage = stage
            self._detail = detail

    def submit_code(self, code):
        value = (code or "").strip()
        if not value or len(value) > 8192 or any(ord(c) < 32 or ord(c) == 127 for c in value):
            raise ValueError("\u6388\u6743\u7801\u5fc5\u987b\u662f\u5355\u884c\u6587\u672c\uff0c\u4e0d\u8981\u7c98\u8d34\u7f51\u9875 URL\u3002")
        if value.startswith(("http://", "https://")):
            raise ValueError("\u8bf7\u53ea\u7c98\u8d34\u6388\u6743\u7801\uff0c\u4e0d\u662f\u6574\u4e2a\u56de\u8c03\u5730\u5740\u3002")
        with self._mutex:
            if self._stage != "WAITING_CODE" or self._process is None:
                raise RuntimeError("\u539f\u767b\u5f55\u8fdb\u7a0b\u672a\u5728\u7b49\u5f85\u6388\u6743\u7801\uff1b\u8bf7\u91cd\u65b0\u8fde\u63a5\u3002")
            self._submitted.append(value)
            self._process.write_line(value)
            self._stage = "VERIFYING"

    def cancel(self):
        self._cancel.set()
        # Killing/reaping is performed by the worker; UI must never block on wait().

    def _one_turn(self, allow_auth):
        from .antigravity_client import _parse_json_output, _json_objects
        args = ["--output-format", "stream-json", "--print-timeout", f"{self.timeout}s",
                "--prompt", "Connection check only. Reply OK. Do not call tools, read files or generate images."]
        if self.model:
            args += ["--model", self.model]
        # Verification must be genuinely headless: a TTY makes agy enter its
        # local interactive OAuth flow and open a browser when the cached
        # credential is unavailable. The explicit compatibility login action
        # opts into the TTY only for its first authorization turn; the fresh
        # credential-reuse check remains headless so it cannot open a second
        # browser flow.
        process = self._factory(
            self.cli, args, cwd=self.cwd, env=runtime_env(self.cli),
            use_tty=bool(self.allow_interactive and allow_auth),
        )
        with self._mutex:
            self._process = process
        raw = ""
        scanned = ""
        try:
            while True:
                chunk = process.read_available()
                raw += chunk
                # Process incremental prompts, including prompts WITHOUT a newline.
                # Inspect only newly arrived text so an old 'paste code' prompt
                # cannot re-enable code submission after it was already submitted.
                if chunk:
                    overlap = strip_ansi(scanned[-160:])
                    window = strip_ansi(scanned[-160:] + chunk)
                    url = official_auth_url(raw, complete_only=True)
                    if url and url != self._url:
                        with self._mutex:
                            self._url = url
                            self._auth_seen = True
                        if not allow_auth:
                            raise RuntimeError("AUTH_NOT_PERSISTED" if self.allow_interactive else "LOGIN_REQUIRED")
                        if self.snapshot()["stage"] != "WAITING_CODE":
                            self._set("WAITING_BROWSER")
                    new_code_prompt = any(m.end() > len(overlap) for m in CODE_PROMPT.finditer(window))
                    if new_code_prompt:
                        self._auth_seen = True
                        if not allow_auth:
                            raise RuntimeError("AUTH_NOT_PERSISTED" if self.allow_interactive else "LOGIN_REQUIRED")
                        self._set("WAITING_CODE")
                    # AGY 1.1.x may emit a transient "not logged in" diagnostic
                    # before the macOS Keychain token finishes loading. A real
                    # interactive login is identified by its URL/code prompt;
                    # otherwise wait for the terminal JSON result below.
                    if SETUP_PROMPT.search(window):
                        self._set("TERMINAL_REQUIRED")
                        raise RuntimeError("TERMINAL_REQUIRED")
                    scanned += chunk
                if self._cancel.is_set():
                    raise RuntimeError("CANCELED")
                if time.monotonic() - self._started > self.timeout:
                    raise RuntimeError("AUTH_TIMEOUT")
                if process.proc.poll() is not None:
                    process._reader.join(timeout=1)
                    raw += process.read_available()
                    break
                time.sleep(0.04)
            text = strip_ansi(raw)
            self._auth_seen = bool(self._auth_seen or CODE_PROMPT.search(text) or official_auth_url(text))
            for obj in _json_objects(text):
                if obj.get("event") == "init":
                    tools = obj.get("init", {}).get("tools")
                    if isinstance(tools, list):
                        self._tools = any("generate_image" == (t if isinstance(t, str) else t.get("name")) for t in tools)
            data = _parse_json_output(text)
            success = process.proc.returncode == 0 and str(data.get("status", "")).upper() == "SUCCESS" and not data.get("error")
            if not success:
                error = str(data.get("error") or "")
                # A model/quota/network error after OAuth is still that error.
                # The earlier browser prompt must not hide the terminal result.
                if AUTH_PROMPT.search(error) or (not error and self._auth_seen):
                    raise RuntimeError("AUTH_INCOMPLETE")
                # Store a redacted diagnostic, not the full transcript or auth URL.
                detail = safe_diagnostic(str(data.get("error") or text[-1200:]), self._submitted)
                raise RuntimeError("PROBE_FAILED: " + detail)
            return data
        finally:
            process.close()
            raw = scanned = ""
            with self._mutex:
                self._process = None

    def run(self):
        from .antigravity_client import AntigravityAccountStatus
        Path(self.cwd).mkdir(parents=True, exist_ok=True)
        try:
            self._set("VERIFYING")
            self._one_turn(allow_auth=self.allow_interactive)
            if self._auth_seen:
                self._set("VERIFYING_REUSE")
                self._url = ""
                self._one_turn(allow_auth=False)
            self._set("SUCCESS")
            message = "AGY \u8fde\u63a5\u5df2\u9a8c\u8bc1\u3002"
            if self._tools is False:
                message += " \u5f53\u524d\u4f1a\u8bdd\u672a\u5217\u51fa generate_image\uff1b\u767b\u5f55\u6210\u529f\u4e0d\u7b49\u4e8e\u751f\u56fe\u6743\u9650\u53ef\u7528\u3002"
            return AntigravityAccountStatus(True, True, self.cli, self.version, "Google OAuth", message, "LOGGED_IN")
        except Exception as exc:
            reason = str(exc)
            messages = {
                "LOGIN_REQUIRED": "AGY 尚未提供可复用的登录。请点‘Google 登录’，在官方终端完成设置和浏览器授权，再点‘验证登录’。",
                "CANCELED": "\u5df2\u53d6\u6d88\u672c\u6b21\u8fde\u63a5\uff0c\u65e7\u6388\u6743\u7801\u4e0d\u518d\u63a5\u53d7\u3002",
                "AUTH_NOT_PERSISTED": "\u672c\u6b21\u6388\u6743\u5b8c\u6210\uff0c\u4f46\u65b0 AGY \u8fdb\u7a0b\u4ecd\u8981\u6c42\u767b\u5f55\u3002\u8bf7\u68c0\u67e5 CLI \u7248\u672c\u3001Keychain \u8bbf\u95ee\u548c\u51ed\u636e\u6301\u4e45\u5316\uff1b\u63d2\u4ef6\u4e0d\u4f1a\u4f2a\u62a5\u5df2\u8fde\u63a5\u3002",
                "AUTH_TIMEOUT": "\u767b\u5f55\u7b49\u5f85\u8d85\u65f6\u3002\u7f51\u9875\u6388\u6743\u540e\u82e5\u663e\u793a code\uff0c\u8bf7\u8f93\u5165\u540c\u4e00\u6b21\u8fde\u63a5\u7684\u6388\u6743\u7801\uff1b\u4e0d\u8981\u53e6\u5f00\u4e00\u6b21\u767b\u5f55\u3002",
                "AUTH_INCOMPLETE": "AGY \u672a\u5b8c\u6210\u6388\u6743\u6216 CLI \u5df2\u9000\u51fa\u3002\u53ef\u4ee5\u5728\u7ec8\u7aef\u5b8c\u6210\u9996\u6b21\u767b\u5f55\uff0c\u518d\u56de\u6765\u70b9\u8fde\u63a5\u9a8c\u8bc1\u3002",
                "TERMINAL_REQUIRED": "AGY \u9700\u8981\u9996\u6b21\u4ea4\u4e92\u8bbe\u7f6e\u6216\u5de5\u4f5c\u533a\u4fe1\u4efb\u786e\u8ba4\u3002\u8bf7\u4f7f\u7528\u7ec8\u7aef\u521d\u59cb\u5316\uff0c\u7136\u540e\u8fde\u63a5\u9a8c\u8bc1\u3002",
            }
            detail = messages.get(reason, safe_diagnostic(reason, self._submitted))
            stage = reason if reason in {"CANCELED", "TERMINAL_REQUIRED"} else "ERROR"
            self._set(stage, detail)
            state = "LOGGED_OUT" if reason in {"AUTH_INCOMPLETE", "AUTH_NOT_PERSISTED", "LOGIN_REQUIRED"} else "ERROR"
            return AntigravityAccountStatus(True, False, self.cli, self.version, "Google OAuth", detail, state)
        finally:
            with self._mutex:
                self._url = ""
                self._submitted.clear()
                self._process = None
