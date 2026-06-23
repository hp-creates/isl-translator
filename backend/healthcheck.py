"""Container health check script.

Used by Docker HEALTHCHECK to verify the backend is responsive.
"""

from __future__ import annotations

import sys

import httpx


def main() -> None:
    """Check if the backend health endpoint responds."""
    try:
        response = httpx.get("http://localhost:8000/health", timeout=5.0)
        if response.status_code == 200:
            sys.exit(0)
        else:
            print(f"Health check failed: HTTP {response.status_code}")
            sys.exit(1)
    except Exception as e:
        print(f"Health check failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
