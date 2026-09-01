import base64
import json
import os
import shutil
import time
import urllib.error
import urllib.parse
import urllib.request


USER_AGENT = "eDock-MacroStudio/0.9"
DEFAULT_TIMEOUT = 10.0
DOWNLOAD_CHUNK_SIZE = 65536

try:
    import requests as _requests

    _SESSION = _requests.Session()
    _SESSION.headers.update({"User-Agent": USER_AGENT})
except ImportError:
    _requests = None
    _SESSION = None


def normalize_timeout(value, default_value=DEFAULT_TIMEOUT, minimum=0.5, maximum=3600.0):
    try:
        timeout = float(value)
    except (TypeError, ValueError):
        timeout = float(default_value)
    return max(minimum, min(maximum, timeout))


def parse_header_lines(text):
    headers = {}
    for line in str(text or "").splitlines():
        line = line.strip()
        if not line or ":" not in line:
            continue
        key, _, value = line.partition(":")
        if key.strip():
            headers[key.strip()] = value.strip()
    return headers


def build_form_body(text):
    pairs = []
    for line in str(text or "").splitlines():
        line = line.strip()
        if line and "=" in line:
            key, _, value = line.partition("=")
            pairs.append((key.strip(), value.strip()))
    return urllib.parse.urlencode(pairs)


def build_request_body(values, runtime):
    method = str(values.get("method", "GET") or "GET").strip().upper()
    if method in ("GET", "HEAD"):
        return None

    if str(values.get("body_source", "value") or "value") == "variable":
        if runtime is None or not hasattr(runtime, "vars"):
            raise RuntimeError("Runtime variables are required for network.http_request")
        raw_body = runtime.vars.get(values.get("body_variable"))
    else:
        raw_body = values.get("body_value")

    raw_body = str(raw_body or "")
    if not raw_body:
        return None

    body_type = str(values.get("body_type", "text") or "text").strip().lower()
    if body_type == "json":
        try:
            return json.dumps(json.loads(raw_body))
        except Exception:
            return raw_body
    if body_type == "form":
        return build_form_body(raw_body)
    return raw_body


def extract_json_value(data, path, default=None):
    path = str(path or "").strip()
    if not path:
        return data
    current = data
    for part in path.split("."):
        if not part:
            continue
        if isinstance(current, dict):
            if part not in current:
                return default
            current = current[part]
        elif isinstance(current, list):
            try:
                current = current[int(part)]
            except Exception:
                return default
        else:
            return default
    return current


def build_webhook_payload(style, message, title="", username=""):
    style = str(style or "generic").strip().lower()
    message = str(message or "")
    title = str(title or "").strip()
    if style == "discord":
        payload = {"content": message}
        username = str(username or "").strip()
        if username:
            payload["username"] = username
        if title:
            payload["embeds"] = [{"title": title}]
        return payload
    if style == "slack":
        text = f"*{title}*\n{message}" if title else message
        return {"text": text}
    if style == "telegram":
        text = f"{title}\n{message}" if title else message
        return {"text": text}
    payload = {"text": message}
    if title:
        payload["title"] = title
    return payload


def _urllib_request(method, url, headers, body, timeout, basic_auth):
    data = None
    if body is not None:
        data = body.encode("utf-8") if isinstance(body, str) else body
    request = urllib.request.Request(url, data=data, method=method)
    for key, value in headers.items():
        request.add_header(key, value)
    if basic_auth is not None:
        token = base64.b64encode(f"{basic_auth[0]}:{basic_auth[1]}".encode("utf-8")).decode("ascii")
        request.add_header("Authorization", f"Basic {token}")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
            return {
                "ok": 200 <= response.status < 400,
                "status": response.status,
                "headers": dict(response.headers.items()),
                "body": raw.decode("utf-8", errors="replace"),
                "url": response.geturl(),
            }
    except urllib.error.HTTPError as error:
        raw = error.read() or b""
        return {
            "ok": False,
            "status": error.code,
            "headers": dict(error.headers.items()) if error.headers else {},
            "body": raw.decode("utf-8", errors="replace"),
            "url": url,
        }


def http_request(method, url, headers=None, body=None, timeout=DEFAULT_TIMEOUT, basic_auth=None):
    method = str(method or "GET").strip().upper()
    url = str(url or "").strip()
    if not url:
        raise ValueError("URL is required")
    if not url.lower().startswith(("http://", "https://")):
        raise ValueError("URL must start with http:// or https://")

    merged_headers = {"User-Agent": USER_AGENT}
    merged_headers.update(dict(headers or {}))
    started = time.monotonic()

    if _SESSION is not None:
        try:
            response = _SESSION.request(
                method,
                url,
                headers=merged_headers,
                data=body,
                timeout=timeout,
                auth=basic_auth,
                allow_redirects=True,
            )
            result = {
                "ok": response.ok,
                "status": response.status_code,
                "headers": dict(response.headers.items()),
                "body": response.text,
                "url": response.url,
            }
        except Exception as error:
            raise ValueError(f"HTTP request failed: {error}")
    else:
        try:
            result = _urllib_request(method, url, merged_headers, body, timeout, basic_auth)
        except ValueError:
            raise
        except Exception as error:
            raise ValueError(f"HTTP request failed: {error}")

    result["method"] = method
    result["elapsed_ms"] = round((time.monotonic() - started) * 1000, 1)
    return result


def resolve_conflict_path(save_path, conflict_rule):
    if str(conflict_rule or "overwrite").strip().lower() != "auto_rename":
        return save_path
    if not os.path.exists(save_path):
        return save_path
    base, extension = os.path.splitext(save_path)
    counter = 1
    while os.path.exists(f"{base} ({counter}){extension}"):
        counter += 1
    return f"{base} ({counter}){extension}"


def download_file(url, save_path, timeout=None, headers=None, conflict_rule="overwrite"):
    url = str(url or "").strip()
    save_path = str(save_path or "").strip()
    if not url:
        raise ValueError("URL is required")
    if not url.lower().startswith(("http://", "https://")):
        raise ValueError("URL must start with http:// or https://")
    if not save_path:
        raise ValueError("Save path is required")
    if timeout is not None:
        timeout = float(timeout)

    save_path = os.path.abspath(resolve_conflict_path(save_path, conflict_rule))
    parent = os.path.dirname(save_path)
    if parent:
        os.makedirs(parent, exist_ok=True)

    merged_headers = {"User-Agent": USER_AGENT}
    merged_headers.update(dict(headers or {}))

    if _SESSION is not None:
        try:
            with _SESSION.get(url, headers=merged_headers, timeout=timeout, stream=True) as response:
                if response.status_code >= 400:
                    raise ValueError(f"Download failed with status {response.status_code}")
                with open(save_path, "wb") as file:
                    for chunk in response.iter_content(chunk_size=DOWNLOAD_CHUNK_SIZE):
                        if chunk:
                            file.write(chunk)
        except ValueError:
            raise
        except Exception as error:
            raise ValueError(f"Download failed: {error}")
    else:
        try:
            request = urllib.request.Request(url, headers=merged_headers)
            if timeout is None:
                with urllib.request.urlopen(request) as response:
                    with open(save_path, "wb") as file:
                        shutil.copyfileobj(response, file, DOWNLOAD_CHUNK_SIZE)
            else:
                with urllib.request.urlopen(request, timeout=timeout) as response:
                    with open(save_path, "wb") as file:
                        shutil.copyfileobj(response, file, DOWNLOAD_CHUNK_SIZE)
        except ValueError:
            raise
        except Exception as error:
            raise ValueError(f"Download failed: {error}")

    file_name = os.path.basename(save_path)
    return {
        "state": "success",
        "file_path": save_path,
        "file_size": os.path.getsize(save_path),
        "file_name": file_name,
        "extension": os.path.splitext(file_name)[1].lstrip(".").lower(),
    }


USER_AGENT_OPTIONS = [
    {"value": "default", "title": "Macro Studio (Default)"},
    {"value": "chrome", "title": "Chrome (Windows)"},
    {"value": "firefox", "title": "Firefox (Windows)"},
    {"value": "edge", "title": "Edge (Windows)"},
    {"value": "safari", "title": "Safari (macOS)"},
    {"value": "postman", "title": "Postman Runtime"},
    {"value": "curl", "title": "curl"},
    {"value": "python", "title": "Python Requests"},
    {"value": "custom", "title": "Custom"},
]

USER_AGENTS = {
    "chrome": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "firefox": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:130.0) Gecko/20100101 Firefox/130.0",
    "edge": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0",
    "safari": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.6 Safari/605.1.15",
    "postman": "PostmanRuntime/7.43.0",
    "curl": "curl/8.9.1",
    "python": "python-requests/2.32.3",
}


def apply_user_agent(values, headers):
    choice = str(values.get("user_agent", "default") or "default").strip().lower()
    agent = USER_AGENTS.get(choice)
    if agent is None and choice == "custom":
        agent = str(values.get("custom_user_agent", "") or "").strip()
    if agent:
        headers["User-Agent"] = agent
    return headers


def resolve_source(values, runtime, base, label=None):
    source = str(values.get(f"{base}_source", "value") or "value")
    if source == "variable":
        if runtime is None or not hasattr(runtime, "vars"):
            raise RuntimeError("Runtime variables are required for this network command")
        value = runtime.vars.get(values.get(f"{base}_variable"))
    else:
        value = values.get(base)
    value = "" if value is None else str(value)
    if label and not value.strip():
        raise ValueError(f"{label} is required")
    return value


def build_multipart_body(form_fields, file_path, file_field_name):
    boundary = "----eDockMacroStudio" + os.urandom(8).hex()
    parts = []
    for line in str(form_fields or "").splitlines():
        line = line.strip()
        if line and "=" in line:
            name, _, value = line.partition("=")
            parts.append(
                f'--{boundary}\r\nContent-Disposition: form-data; name="{name.strip()}"\r\n\r\n{value.strip()}\r\n'.encode("utf-8")
            )
    with open(file_path, "rb") as file:
        content = file.read()
    file_name = os.path.basename(file_path)
    parts.append(
        (
            f'--{boundary}\r\nContent-Disposition: form-data; name="{file_field_name}"; filename="{file_name}"\r\n'
            "Content-Type: application/octet-stream\r\n\r\n"
        ).encode("utf-8")
        + content
        + b"\r\n"
    )
    parts.append(f"--{boundary}--\r\n".encode("utf-8"))
    return boundary, b"".join(parts)
