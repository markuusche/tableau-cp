import yaml
import pyotp
import os, ast
import shutil
import getpass
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class Helper:

    #locator fetch helper 
    def data(self, *keys):
        with open('src/locators.yaml','r') as file:
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

        os.makedirs(weekly_folder, exist_ok=True)
        os.makedirs(daily_folder, exist_ok=True)

        files = self.renameFiles('file_names')
        file_renames = files

        for original_name in file_renames.keys():
            source_path = os.path.join(downloads, original_name)

            if os.path.exists(source_path):
                if self.env("dg1") in original_name:
                    target_folder = weekly_folder
                elif self.env("dg") in original_name or self.env("st") in original_name:
                    target_folder = daily_folder
                else:
                    continue

                destination = get_unique_path(target_folder, original_name)
                shutil.move(source_path, destination)
                print(f"Moved: {original_name} → {destination}")
            else:
                print(f"File not found: {original_name}")

    # rename the files 
    def modifyFiles(self, fileNames={}):
        base_downloads = os.path.expanduser("~/Downloads")
        daily_folder = os.path.join(base_downloads, "daily")
        weekly_folder = os.path.join(base_downloads, "weekly")

        # rename files in daily and weekly folders
        file_renames = fileNames
        for old_name, new_name in file_renames.items():
            # daily
            old_path = os.path.join(daily_folder, old_name)
            if os.path.exists(old_path):
                new_path = os.path.join(daily_folder, new_name)
                os.rename(old_path, new_path)
                print(f"Renamed in daily: {old_name} → {new_name}")
                continue  

            # weekly
            old_path = os.path.join(weekly_folder, old_name)
            if os.path.exists(old_path):
                new_path = os.path.join(weekly_folder, new_name)
                os.rename(old_path, new_path)
                print(f"Renamed in weekly: {old_name} → {new_name}")
            else:
                print(f"File not found in either folder: {old_name}")
    
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
