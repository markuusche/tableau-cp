import time
import pytest
from selenium import webdriver
from src.helpers.helper import Helpers

@pytest.fixture(scope="session")
def driver(): 
    port = "9333"
    option = webdriver.ChromeOptions()
    option.add_experimental_option("debuggerAddress", f"127.0.0.1:{port}")
    try:
        driver = webdriver.Chrome(options=option)
        driver.execute_cdp_cmd("Network.clearBrowserCache", {})
        driver.maximize_window()
        driver.get(Helpers.env('main'))
        time.sleep(20) # time needed to manually scan QR on the web
        yield driver
    except Exception as e:
        pytest.fail(f"Could not connect to browser on port {port}. check launcher.py? Exception: {e}")
