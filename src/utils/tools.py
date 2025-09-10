from time import sleep
from src.helpers.helper import Helpers
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class Tools(Helpers):
    
    # login user
    def userLogin(self, driver):
        driver.execute_script("return document.readyState") == "complete"
        self.wait_element(driver, 'login', 'user')
        user = self.search_element(driver, 'login', 'user')
        user.send_keys(self.env('email'))
        password = self.search_element(driver, 'login', 'pass')
        password.send_keys(self.env('pass'))
        self.search_element(driver, 'login', 'submit', click=True)
        self.wait_element(driver, 'dashboard', 'panel')
        
    # switch to iframe    
    def _iframe(self, driver):
        iframe = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.TAG_NAME, "iframe"))
        )
        driver.switch_to.frame(iframe)
        self.wait_element(driver, 'table', 'data', timeout=10)
        
    def singlePage(self, driver, data, promo: bool = False):
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
    def download(self, driver):
        driver.execute_script("return document.readyState") == "complete"
        self.wait_element(driver, 'table', 'toolbar', timeout=10)
        driver.execute_script('document.querySelector("#viz-viewer-toolbar > div:last-child #download").click();')
        self.wait_element(driver, 'table', 'download', timeout=10)
        driver.execute_script("return document.readyState") == "complete"

        # very stupid flaky 
        while True:
            try:
                self.wait_clickable(driver, 'table', 'crosstab', timeout=5)
                break
            except:
                self.wait_element(driver, 'table', 'download')
                continue
        
        driver.execute_script("return document.readyState") == "complete"
            
        # very very stupid flaky
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
        
        # another flaky guy
        while True:
            try:
                self.search_element(driver, 'table', 'csv', click=True)
                break
            except:
                continue
    
        self.search_element(driver, 'table', 'btn', click=True)
        self.wait_element_invisibility(driver, 'table', 'pop-up')
        sleep(2)
