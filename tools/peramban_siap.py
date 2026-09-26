from __future__ import annotations

import sys


def siap() -> bool:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return False

    try:
        with sync_playwright() as p:
            peramban = p.chromium.launch()
            peramban.close()
    except Exception:
        return False
    return True


if __name__ == "__main__":
    sys.exit(0 if siap() else 1)
