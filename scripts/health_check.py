"""
health_check.py — JBK-OS Health Check Validator

PURPOSE:
    Validates that the JBK-OS web server health endpoint responds correctly.
    Used by:
      - Docker HEALTHCHECK instruction
      - Cloud Run liveness and readiness probes (via HTTP GET /health)
      - CI pipeline post-startup validation

USAGE:
    python scripts/health_check.py                     # Check default localhost:8080
    python scripts/health_check.py http://host:port    # Check specific target

EXIT CODES:
    0 — Health endpoint returned 200 OK
    1 — Health endpoint unreachable or returned non-200 status
"""

from __future__ import annotations

import sys
import json
import urllib.request
import urllib.error


DEFAULT_URL = "http://localhost:8080/health"
TIMEOUT_SECONDS = 5


def check_health(url: str) -> tuple[bool, str]:
    """Perform an HTTP GET request to the health endpoint.

    Returns:
        (success: bool, message: str)
    """
    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT_SECONDS) as response:
            status_code = response.status
            body = response.read().decode("utf-8", errors="replace")

            if status_code == 200:
                return True, f"HEALTHY — HTTP {status_code} from {url}"
            else:
                return False, f"UNHEALTHY — HTTP {status_code} from {url}: {body[:200]}"

    except urllib.error.HTTPError as exc:
        return False, f"UNHEALTHY — HTTP {exc.code} from {url}: {exc.reason}"
    except urllib.error.URLError as exc:
        return False, f"UNREACHABLE — {url}: {exc.reason}"
    except TimeoutError:
        return False, f"TIMEOUT — No response from {url} within {TIMEOUT_SECONDS}s"
    except Exception as exc:  # noqa: BLE001
        return False, f"ERROR — {type(exc).__name__}: {exc}"


def main() -> int:
    """Entry point. Returns 0 on success, 1 on failure."""
    url = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_URL

    success, message = check_health(url)

    result = {
        "status": "healthy" if success else "unhealthy",
        "endpoint": url,
        "message": message,
    }

    # Structured JSON output for Cloud Logging ingestion
    print(json.dumps(result))

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
