import os
import yaml
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class Helpers:
    
  
    #locator fetch helper 
    def data(self, *keys):
        with open('src/config/locators.yaml','r') as file:
            getData = yaml.load(file, Loader=yaml.FullLoader)

        for key in keys:
            getData = getData[key]

        return getData
    
    # get bashrc value
    def env(self, key, is_list=False):
        if is_list:
            raw = os.environ.get(key)
            value = raw.split(":")
        else:
            value = os.environ.get(key)

        return value

    # selenium function helper
    def search_element(self, driver, *keys, click=False):
        locator = self.data(*keys)
        element = driver.find_element(By.CSS_SELECTOR, locator)
        if click:
            element.click()
        else:
            return element

    def wait_element(self, driver, *keys, timeout=60):
        path = (By.CSS_SELECTOR, self.data(*keys))
        element = WebDriverWait(driver, timeout)
        element.until(EC.visibility_of_element_located(path))
    
    def wait_element_invisibility(self, driver, *keys, absolute=False, timeout=120):
        try:
            locator = (By.CSS_SELECTOR, self.data(*keys))
            element = WebDriverWait(driver, timeout)
            if absolute:
                element.until(EC.invisibility_of_element_located(locator))
            else:  
                element.until(EC.invisibility_of_element(locator))
        except:
            print(f'\033[91m[ FAILED ] "{locator}" element still diplayed.')
    
    def wait_clickable(self, driver, *keys, timeout=60):
        locator = (By.CSS_SELECTOR, self.data(*keys))
        wait = WebDriverWait(driver, timeout)
        element = wait.until(EC.element_to_be_clickable(locator),
        message=f'\033[91m[ FAILED ] "{locator}" element was not clickable.')
        element.click()
