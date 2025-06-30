import yaml
import pyotp
import os, ast
import shutil
import getpass
import re
from time import sleep
from zoneinfo import ZoneInfo
from datetime import datetime, timedelta
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class Helper:

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

    # rename file(s)?
    def renameFiles(self, file):
        file_names = self.env(file)
        names = ast.literal_eval(file_names) if file_names else {}
        return names
    
    # about files
    def moveFiles(self):

        def get_clean_basename(filename):
            base, ext = os.path.splitext(filename)
            base = re.sub(r'\s\(\d+\)$', '', base)
            return base + ext

        # path
        def get_unique_path(folder, filename):
            clean_name = get_clean_basename(filename)
            base, ext = os.path.splitext(clean_name)
            candidate = clean_name
            counter = 1
            while os.path.exists(os.path.join(folder, candidate)):
                candidate = f"{base} ({counter}){ext}"
                counter += 1
            return os.path.join(folder, candidate)

        user = getpass.getuser()
        downloads = os.path.expanduser("~/Downloads")
        weekly_folder = f"/Users/{user}/Downloads/weekly"
        daily_folder = f"/Users/{user}/Downloads/daily"
        stats_folder = os.path.join(downloads, "stats")

        os.makedirs(weekly_folder, exist_ok=True)
        os.makedirs(daily_folder, exist_ok=True)
        os.makedirs(stats_folder, exist_ok=True)

        files = self.renameFiles('file_names')
        file_renames = files

        for original_name in file_renames.keys():
            source_path = os.path.join(downloads, original_name)
            daily_target_path = os.path.join(daily_folder, original_name)

            if os.path.exists(source_path):
                
                if self.env("st") in original_name and os.path.exists(daily_target_path):
                    continue

                if self.env("dg1") in original_name:
                    target_folder = weekly_folder
                elif self.env("dg") in original_name or self.env("st") in original_name:
                    target_folder = daily_folder
                else:
                    continue

                destination = get_unique_path(target_folder, original_name)
                shutil.move(source_path, destination)
            else:
                print(f"File not found: {original_name}")
        
        # move stats file separately to a folder
        for filename in os.listdir(downloads):
            filepath = os.path.join(downloads, filename)
            if os.path.isfile(filepath) and filename.startswith(self.env("st")):
                destination = os.path.join(stats_folder, filename)
                shutil.move(filepath, destination)
    
    # rename the files 
    def modifyFiles(self):
        base_downloads = os.path.expanduser("~/Downloads")
        folders = {
            'file_names': os.path.join(base_downloads, "daily"),
            'weekly_names': os.path.join(base_downloads, "weekly"),
            'stats_week_names': os.path.join(base_downloads, "stats"),
        }

        def rename(folder, old_name, new_name):
            old_path = os.path.join(folder, old_name)
            if os.path.exists(old_path):
                new_path = os.path.join(folder, new_name)
                os.rename(old_path, new_path)

        for env_key, folder_path in folders.items():
            file_map = ast.literal_eval(self.env(env_key) or "{}")
            for old, new in file_map.items():
                rename(folder_path, old, new)

     # filters items from the list
    def filterList(self, value):
        value = value.replace("IP_", "").replace("IP", "").strip()
        value = re.sub(r'(FC)$', r' \1', value).strip()

        provider_mapping = {
            "CAS": self.env("CAS"),
            "GAM": self.env("GAM")
        }

        match = re.match(r"^([A-Z]{2,3})(.*?)([A-Z]{2,})$", value)
        if match:
            raw_provider, game_name, vendor = match.groups()
            provider = provider_mapping.get(raw_provider, raw_provider)

            game_name = game_name.replace("INO GAME", "").strip()
            if game_name.endswith(self.env("EV")):
                game_name = game_name[:-len(self.env("EV"))].strip()
                vendor = f"{self.env("EVE")} {vendor}"
            
            for unwanted in ["INO GAME", "E SHOW"]:
                game_name = game_name.replace(unwanted, "").strip()
            
            if not game_name and re.match(r"[A-Z]{3,}[A-Z]{2,}$", vendor):
                split_match = re.match(r"^([A-Z]+?)([A-Z]{2,})$", vendor)
                if split_match:
                    game_name, vendor = split_match.groups()
            
            vendor_prefixes = ["XL", "X", "CAISHEN", "II", "WINS", "ILO", "DNT", "I"] # in case need to filter more
            for prefix in vendor_prefixes:
                if vendor.startswith(prefix):
                    game_name = f"{game_name} {prefix}".strip()
                    vendor = vendor[len(prefix):].strip()
                    break

            vendor = vendor.replace("_", " ").strip()
            return [provider, game_name, vendor]

        match2 = re.match(r"^(.*?)([A-Z]{2,})$", value)
        if match2:
            game_name, vendor = match2.groups()
            return [provider_mapping.get("CAS", self.env("CAS")), game_name.strip(), vendor.strip()]

        return [provider_mapping.get(value.strip(), value.strip())]

    # clear daily/weekly folder
    def clearFolders(self):
        user = getpass.getuser()
        downloads = f"/Users/{user}/Downloads"
        folders = [os.path.join(downloads, "daily"), os.path.join(downloads, "weekly")]

        for folder in folders:
            if os.path.exists(folder):
                shutil.rmtree(folder)
                print(f"Deleted folder: {folder}")
            else:
                print(f"Folder does not exist: {folder}")

    # get weeks/day info
    def getWeekInfo(self):
        today = datetime.now(ZoneInfo("Asia/Manila"))
        date_str = today.strftime("%Y-%m-%d")
        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
        weekday_index = date_obj.weekday()

        monday = today - timedelta(days=7)
        sunday = today - timedelta(days=1)

        full_week = [(monday + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]

        # check if the day today is the first day of the month? stupid
        last_month_dates = []
        if date_obj.day == 30:
            first_of_last_month = (date_obj.replace(day=1) - timedelta(days=1)).replace(day=1)
            last_of_last_month = date_obj.replace(day=1) - timedelta(days=1)
            last_month_dates = [
                (first_of_last_month + timedelta(days=i)).strftime("%Y-%m-%d")
                for i in range((last_of_last_month - first_of_last_month).days + 1)
            ]

        return {
            "today": date_str,
            "weekday_index": weekday_index,
            "monday": monday.strftime("%Y-%m-%d"),
            "sunday": sunday.strftime("%Y-%m-%d"),
            "full_week": full_week,
            "last_month_dates": last_month_dates
        }
    
    # download data page
    def download(self, driver):
        ## ============== STOPPED HERE == !@!!
        cursor = self.search_element(driver, 'table', 'glass')
        WebDriverWait(driver, 20).until(lambda a: cursor.value_of_css_property("cursor") == "default")
        self.wait_clickable(driver, 'table', 'download-btn')
        # driver.execute_script('document.querySelector("#viz-viewer-toolbar > div:last-child #download").click();')
        self.wait_element(driver, 'table', 'download')
        self.search_element(driver, 'table', 'crosstab', click=True)
        self.wait_element(driver, 'table', 'pop-up')
        self.search_element(driver, 'table', 'csv', click=True)
        self.search_element(driver, 'table', 'btn', click=True)
        sleep(2)

    # authentication keys for game providers
    def getOTP(self):
        totp = pyotp.TOTP(self.env('otpKey'))
        otp = totp.now()
        return otp

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
