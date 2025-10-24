import os
import yaml
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC

class Helpers:
    
    @staticmethod 
    def data(*keys) -> str:
        with open('src/config/locators.yaml','r') as file:
            getData = yaml.load(file, Loader=yaml.FullLoader)

        for key in keys:
            getData = getData[key]

        return getData
    
    @staticmethod
    def env(key: str, is_list: bool = False) -> list[str] | None:
        data = os.environ.get(key)
        if data is None:
            return [] if is_list else ""
        return data.split(':') if is_list else data

    # selenium function helper
    def search_element(self, driver, *keys, click: bool = False) -> WebElement:
        locator = self.data(*keys)
        element = driver.find_element(By.CSS_SELECTOR, locator)
        return element if not click else element.click()

    def wait_element(self, driver, *keys, timeout: int = 60) -> None:
        path = (By.CSS_SELECTOR, self.data(*keys))
        element = WebDriverWait(driver, timeout)
        element.until(EC.visibility_of_element_located(path))
    
    def wait_element_invisibility(self, driver, *keys, absolute: bool = False, timeout: int = 120) -> None:
        try:
            locator = (By.CSS_SELECTOR, self.data(*keys))
            element = WebDriverWait(driver, timeout)
            if absolute:
                element.until(EC.invisibility_of_element_located(locator))
            else:  
                element.until(EC.invisibility_of_element(locator))
        except:
            print(f'\033[91m[ FAILED ] "{locator}" element still diplayed.')
    
    def wait_clickable(self, driver, *keys, timeout: int = 60) -> None:
        locator = (By.CSS_SELECTOR, self.data(*keys))
        wait = WebDriverWait(driver, timeout)
        element = wait.until(EC.element_to_be_clickable(locator),
        message=f'\033[91m[ FAILED ] "{locator}" element was not clickable.')
        element.click()
