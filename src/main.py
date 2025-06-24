import csv
import os, ast
from pathlib import Path
from time import sleep
from pathlib import Path
from zoneinfo import ZoneInfo  
from src.helper.utils import Helper
from src.api.sheet import GoogleSheet
from datetime import datetime, timedelta
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC

class Tableau(Helper):

    def __init__(self):
        self.sheet = GoogleSheet()
        self.files = self.env('files', True)
        self.week_files = self.env('week_files', True)
        self.downloads = os.path.expanduser("~/Downloads")

    def mondayCheck(self):
        # get last week's date
        today = datetime.now(ZoneInfo("Asia/Manila"))
        last_monday = today - timedelta(days=7)
        last_sunday = today - timedelta(days=1)

        date_str = today.strftime("%Y-%m-%d")
        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
        return date_obj.weekday(), last_monday, last_sunday

    def navigate(self, driver):

        def download():
            driver.execute_script('document.querySelector("#viz-viewer-toolbar > div:last-child #download").click();')
            self.wait_element(driver, 'table', 'download')
            self.search_element(driver, 'table', 'crosstab', click=True)
            self.wait_element(driver, 'table', 'pop-up')
            self.search_element(driver, 'table', 'csv', click=True)
            self.search_element(driver, 'table', 'btn', click=True)

        # data table page
        iframe = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.TAG_NAME, "iframe"))
        )
        driver.switch_to.frame(iframe)
        self.wait_element(driver, 'table', 'data', timeout=180)
        download()
        today, last_monday, last_sunday = self.mondayCheck()
        if today == 0:
            self.wait_element(driver, 'table', 'date-1')
            dates = {
                    'date-1': last_monday.strftime("%Y-%m-%d"),
                    'date-2': last_sunday.strftime("%Y-%m-%d")
                    }

            for key, val in dates.items():
                setDate = self.search_element(driver, 'table', key)
                setDate.send_keys(Keys.COMMAND, 'a')
                setDate.send_keys(Keys.BACKSPACE)
                setDate.send_keys(val)

            setDate = self.search_element(driver, 'table', 'date-2')
            setDate.send_keys(Keys.ENTER)
            sleep(7)
            download()
        sleep(2)
        self.moveFiles()

    # login user
    def userLogin(self, driver):
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

    def gameData(self):

        # rename the files
        names = ['file_names', 'weekly_names']
        for name in names:
            x = self.env(name)
            y = ast.literal_eval(x) if x else {}
            self.modifyFiles(y)

        def sample(mode, stats, theFiles):
            target = Path.home() / f"Downloads/{mode}"
            for name in theFiles:

                temp = []

                file = target / name
                if not file.exists():
                    continue

                with open(file, newline='', encoding='utf-16') as csvfile:
                    reader = csv.reader(csvfile, delimiter='\t')
                    for i, row in enumerate(reader):
                        if i < 2 and name != self.env(stats):
                            continue
                        if i < 1 and name == self.env(stats):
                            continue
                        if not row:
                            continue

                        new_cols = self.filterList(row[0])
                        remaining_cols = row[1:]
                        row = new_cols + remaining_cols
                        temp.append(row)

                if name != stats:
                    cleaned_temp = []

                    for row in temp:
                        if len(row) > 4:
                            date_range = f"{row[3]} - {row[4]}"
                        else:
                            date_range = row[3] if len(row) > 3 else ""

                        new_row = row.copy()
                        new_row[3] = date_range
                        del new_row[4]
                        cleaned_temp.append(new_row)

                    filtered_data = []
                    removeIndex = {4, 5, 6, 7}

                    today, _, _ = self.mondayCheck()
                    dataList = cleaned_temp if today == 0 else temp

                    for row in dataList:
                        moved_value = row[3] if len(row) > 3 else None
                        cleaned_row = [val for idx, val in enumerate(row) if idx not in removeIndex and idx != 3]
                        if moved_value is not None:
                            cleaned_row.insert(0, moved_value)
                        filtered_data.append(cleaned_row)

                    temp = filtered_data

                # print(temp)

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

        sample("daily", "stats", self.files)
        sample("weekly", "week_stats", self.week_files)

        self.clearFolders()

