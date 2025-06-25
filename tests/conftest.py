import pytest
from selenium import webdriver
from src.utils.helper import Helper

@pytest.fixture(scope='session')
def driver():
    #setup
    URL = Helper()
    option = webdriver.ChromeOptions()
    option.add_argument("--hide-scrollbars")
    option.add_argument("--mute-audio")
    option.add_argument("--no-sandbox")
    option.add_argument("--log-level=3")
    option.add_argument("--disable-logging")
    option.add_argument("--disable-software-rasterizer")
    option.add_argument("--enable-unsafe-swiftshader")
    option.add_argument("--disable-dev-shm-usage")
    option.add_argument("--disable-infobars")
    option.add_argument("--disable-extensions")
    option.add_argument("--disable-popup-blocking")
    option.add_experimental_option("excludeSwitches",["enable-automation"])
    option.add_experimental_option('useAutomationExtension', False)
    option.add_experimental_option("prefs", {
            "credentials_enable_service": False,      
            "profile.password_manager_enabled": False,
            "profile.password_manager_leak_detection": False,
            "profile.default_content_setting_values.notifications": 2
        })
    driver = webdriver.Chrome(options=option)
    driver.maximize_window()
    driver.get(URL.env('main'))

    yield driver
        
    #teardown
    driver.close()
    driver.quit()
