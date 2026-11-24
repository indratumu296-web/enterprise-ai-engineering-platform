from __future__ import annotations

import time
from typing import Any

import requests


class APIRequestError(RuntimeError):
    """An API request failed after validation or retry handling."""


def request_json(
    method: str,
    url: str,
    *,
    retries: int = 3,
    timeout: float = 5,
    **kwargs: Any,
) -> Any:
    if retries < 1:
        raise ValueError("retries must be at least 1")
    for attempt in range(retries):
        try:
            response = requests.request(method, url, timeout=timeout, **kwargs)
            response.raise_for_status()
            if response.status_code == 204:
                return None
            return response.json()
        except requests.HTTPError as exc:
            status_code = exc.response.status_code if exc.response is not None else None
            retryable_status = status_code == 429 or (status_code is not None and status_code >= 500)
            if not retryable_status or attempt == retries - 1:
                detail = ""
                if exc.response is not None:
                    try:
                        body = exc.response.json()
                        detail = str(body.get("detail", body))
                    except ValueError:
                        detail = exc.response.text
                raise APIRequestError(detail or f"API returned HTTP {status_code}.") from exc
        except requests.RequestException as exc:
            if attempt == retries - 1:
                raise APIRequestError(f"API request failed after {retries} attempts: {exc}") from exc
        time.sleep(0.25 * (attempt + 1))
    raise APIRequestError(f"API request failed after {retries} attempts.")