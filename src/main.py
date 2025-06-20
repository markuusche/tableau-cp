import os, ast
import re
import csv
from time import sleep
from pathlib import Path
from src.helper.utils import Helper
from src.api.sheet import GoogleSheet
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC

class Tableau(Helper):

    def __init__(self):
        self.sheet = GoogleSheet()
        self.files = self.env('files', True)
        self.downloads = os.path.expanduser("~/Downloads")

    def navigate(self, driver):
        # data table page
        iframe = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.TAG_NAME, "iframe"))
        )
        driver.switch_to.frame(iframe)
        self.wait_element(driver, 'table', 'data', timeout=180)
        driver.execute_script('document.querySelector("#viz-viewer-toolbar > div:last-child #download").click();')
        self.wait_element(driver, 'table', 'download')
        self.search_element(driver, 'table', 'crosstab', click=True)
        self.wait_element(driver, 'table', 'pop-up')
        self.search_element(driver, 'table', 'csv', click=True)
        self.search_element(driver, 'table', 'btn', click=True)
        sleep(2)

    def userLogin(self, driver):
        # userLogin
        self.wait_element(driver, 'login', 'email')
        email = self.search_element(driver, 'login', 'email')
        email.send_keys(self.env('email'))
        self.search_element(driver, 'login', 'btn', click=True)
        self.wait_element(driver, 'login', 'cookies')
        self.search_element(driver, 'login', 'cookies', click=True)
        self.wait_element(driver, 'login', 'email')
        password = self.search_element(driver, 'login', 'pass')
        password.send_keys(self.env('pass'))
        self.search_element(driver, 'login', 'sign-in', click=True)
        sleep(7)
        actions = ActionChains(driver)
        key = self.getOTP()
        actions.send_keys(key).perform()
        actions.send_keys(Keys.ENTER).perform()
        self.wait_element(driver, 'dashboard', 'pop-up')

    # Full game report workbook
    def gameReport(self, driver):
        self.userLogin(driver)
        # dashboard
        categories = self.env('categories', True)
        for item in categories:
            driver.get(self.env('tableau') + f"Category={item}")
            self.navigate(driver) 
        
        driver.get(self.env('statistics'))
        self.navigate(driver)

    def modifyFiles(self, fileNames={}):

        # rename downloaded files
        file_renames = fileNames

        for old_name, new_name in file_renames.items():
            old_path = os.path.join(self.downloads, old_name)
            new_path = os.path.join(self.downloads, new_name)
            if os.path.exists(old_path):
                os.rename(old_path, new_path)
            else:
                print(f"\nFile not found: {old_name}")

    def getData(self):

        file_names = self.env('file_names')
        names = ast.literal_eval(file_names) if file_names else {}
        self.modifyFiles(names)
        
        def clean_first_column(value):
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

        target = Path.home() / "Downloads"
        stats = self.env("stats")
        for name in self.files:

            temp = []

            file = target / name
            if not file.exists():
                continue

            with open(file, newline='', encoding='utf-16') as csvfile:
                reader = csv.reader(csvfile, delimiter='\t')
                for i, row in enumerate(reader):
                    if i < 2 and name != stats: 
                        continue
                        
                    if i < 1 and name == stats:
                        continue

                    if not row:
                        continue

                    new_cols = clean_first_column(row[0])
                    remaining_cols = row[1:]

                    row = new_cols + remaining_cols
                    temp.append(row)

            # print(temp)

            if name != stats:
                removeIndex = {4, 5, 6, 7}

                cleaned_temp = []

                for row in temp:
                    moved_value = row[3] if len(row) > 3 else None
                    cleaned_row = [val for idx, val in enumerate(row) if idx not in removeIndex and idx != 3]
                    if moved_value is not None:
                            cleaned_row.insert(0, moved_value)

                    cleaned_temp.append(cleaned_row)

                temp = cleaned_temp

            if name == stats:

                updated_temp = []

                for i, row in enumerate(temp):
                    new_row = row.copy()
                    if i != 0 and len(new_row) > 0:
                        new_row[0] = "" 
                    updated_temp.append(new_row)

                temp = updated_temp

            filter_name = name.replace('.csv','').strip()

            self.sheet.populateSheet(filter_name, f'A2', temp)

        # delete downloaded file
        for filename in self.files:
            file_path = os.path.join(self.downloads, filename)
            if os.path.exists(file_path):
                os.remove(file_path)
            else:
                print(f"\nFile not found: {filename}")

