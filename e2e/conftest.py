"""Fixtures for the E2E suite.

`live_server` boots the actual Flask app (application factory,
same code path as production) in a background thread against a real
port and an isolated temp SQLite file, so Selenium talks to a real
running server exactly like a real user's browser would.

`driver` opens a real Chrome window by default — visual mode, as the
assignment requires for local evidence. Set E2E_HEADLESS=1 (used in
the GitHub Actions pipeline, which has no display) to run headless.
"""

import os
import socket
import sys
import tempfile
import threading
import time

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app  # noqa: E402


def _free_port():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


@pytest.fixture(scope="session")
def live_server():
    db_fd, db_path = tempfile.mkstemp()
    port = _free_port()

    flask_app = create_app(test_config={"DATABASE": db_path, "TESTING": True})

    thread = threading.Thread(
        target=lambda: flask_app.run(
            host="127.0.0.1", port=port, use_reloader=False, threaded=True
        ),
        daemon=True,
    )
    thread.start()
    time.sleep(1)  # give the dev server a moment to bind the socket

    yield f"http://127.0.0.1:{port}"

    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def driver():
    options = Options()

    if os.environ.get("E2E_HEADLESS") == "1":
        options.add_argument("--headless=new")

    options.add_argument("--window-size=1280,900")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    # Optional overrides (normally not needed: Selenium Manager finds Chrome
    # and downloads a matching chromedriver automatically).
    if os.environ.get("CHROME_BIN"):
        options.binary_location = os.environ["CHROME_BIN"]

    service = (
        Service(executable_path=os.environ["CHROMEDRIVER_PATH"])
        if os.environ.get("CHROMEDRIVER_PATH")
        else Service()
    )

    chrome_driver = webdriver.Chrome(service=service, options=options)
    chrome_driver.implicitly_wait(5)

    yield chrome_driver

    chrome_driver.quit()
