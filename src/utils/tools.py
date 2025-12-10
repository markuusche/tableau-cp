import pyotp
from time import sleep
from src.helpers.helper import Helpers
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class Tools(Helpers):
    
    # login user
    def userLogin(self, driver) -> None:

        def getOTP():
            key = self.env("otpKey")
            userOTP = pyotp.TOTP(key)
            return userOTP.now()
        
        driver.execute_script("return document.readyState") == "complete"
        self.wait_element(driver, 'login', 'user')
        user = self.search_element(driver, 'login', 'user')
        user.send_keys(self.env('email'))
        self.search_element(driver, 'login', 'submit', click=True)
        self.wait_element(driver, 'login', 'pass')
        password = self.search_element(driver, 'login', 'pass')
        password.send_keys(self.env('pass'))
        self.search_element(driver, 'login', 'submit', click=True)
        self.wait_element(driver, 'login', 'otp')
        otp = self.search_element(driver, 'login', 'otp')
        
        for _ in range(3):
            try:
                otp.send_keys(getOTP())
                self.search_element(driver, 'login', 'submit', click=True)
                self.wait_element(driver, 'dashboard', 'panel', timeout=5)
                break
            except:
                otp = self.search_element(driver, 'login', 'otp')
                otp.clear()
                sleep(1)
                continue

    # switch to iframe    
    def _iframe(self, driver, selector: str = 'data') -> None:
        iframe = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.TAG_NAME, "iframe"))
        )
        driver.switch_to.frame(iframe)

        try:
            self.wait_element(driver, 'table', selector, timeout=60)
        except:
            pass

    def singlePage(self, driver, data, promo: bool = False) -> None:
        if not promo:
            self._iframe(driver)
        try:
            
            try:
                self.wait_element(driver, 'table', 'data', timeout=180)
            except:
                pass
            
            for date in data:
                setDate = self.search_element(driver, 'table', 'date-s')
                setDate.send_keys(Keys.COMMAND, 'a')
                setDate.send_keys(Keys.BACKSPACE)
                setDate.send_keys(date)
                self.download(driver)
        except:
            pass

    # download data page
    def download(self, driver, data: bool = False, dataIndex: bool = False) -> None:
        
        driver.execute_script("return document.readyState") == "complete"
        self.wait_element_invisibility(driver, 'table', 'processing', timeout=60)
        self.wait_element(driver, 'table', 'download-btn', timeout=10)
        driver.execute_script('document.querySelector("#viz-viewer-toolbar > div:last-child #download").click();')
        self.wait_element(driver, 'table', 'download', timeout=10)
        driver.execute_script("return document.readyState") == "complete"
        
        def wait_until_clickable(key: str):
            while True:
                try:
                    self.wait_clickable(driver, 'table', key, timeout=5)
                    break
                except:
                    self.wait_element(driver, 'table', 'download')
                    continue
                
            driver.execute_script("return document.readyState") == "complete"

        if not data:
            # download is very flaky
            wait_until_clickable('crosstab')
                
            while True:
                try:
                    self.wait_element(driver, 'table', 'pop-up', timeout=5)
                    break
                except:
                    try:
                        self.wait_clickable(driver, 'table', 'crosstab', timeout=5)
                        break
                    except:
                        continue
                    
            if dataIndex:
                self.search_element(driver, 'table' , 'dataIndex', click=True)
            
            while True:
                try:
                    self.search_element(driver, 'table', 'csv', click=True)
                    break
                except:
                    continue
        
            self.search_element(driver, 'table', 'btn', click=True)
            self.wait_element_invisibility(driver, 'table', 'pop-up')
            sleep(2)
        else:
            wait_until_clickable('download data')
            sleep(3)
            main = driver.current_window_handle
            handles = driver.window_handles
            while len(handles) < 1:
                sleep(1)
            else:
                for handle in handles:
                    if handle != main:
                        driver.switch_to.window(handle)
                        driver.execute_script("return document.readyState") == "complete"
                        self.search_element(driver, 'table', 'pop-up data', click=True)
                        self.wait_element(driver, 'table', 'info')
                        sleep(3)
                        driver.close()
                        break
                
                driver.switch_to.window(main)
