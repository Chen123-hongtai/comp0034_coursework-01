"""
Provide pytest fixtures for the end-to-end UI test suite.

This module sets up the testing environment by automatically starting the
Dash application server in a background process before tests run, and safely
terminating the process once all tests are complete.
"""

import pytest
import subprocess
import time
import requests

@pytest.fixture(scope="session", autouse=True)
def start_dash_app():
    """
    Starts the Dash app in a background subprocess before running any tests.
    Tears it down after all tests are complete.
    """
    # Start the app using Python
    process = subprocess.Popen(["python", "app.py"])
    
    # Wait for the server to be ready (timeout after 15 seconds)
    server_url = "http://localhost:8050"
    timeout = 15
    start_time = time.time()
    
    while True:
        try:
            response = requests.get(server_url)
            if response.status_code == 200:
                break
        except requests.exceptions.ConnectionError:
            pass
        
        if time.time() - start_time > timeout:
            process.terminate()
            raise RuntimeError("Dash server failed to start within the timeout period.")
        time.sleep(0.5)
        
    yield server_url  # Provide the URL to the tests
    
    # Teardown: terminate the process after tests finish
    process.terminate()
