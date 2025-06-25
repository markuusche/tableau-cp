import csv
import os, ast
from pathlib import Path
from time import sleep
from pathlib import Path
from zoneinfo import ZoneInfo  
from src.utils.helper import Helper
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
        self.weekly_stats_files = self.env('weekly_stats_files', True)
        self.downloads = os.path.expanduser("~/Downloads")
    
    def _iframe(self, driver):
        iframe = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.TAG_NAME, "iframe"))
        )
        driver.switch_to.frame(iframe)
        self.wait_element(driver, 'table', 'data', timeout=180)
    
    def navigate(self, driver):
        # data table page
        self._iframe(driver)
        self.download(driver)
        info = self.getWeekInfo()
        if info["weekday_index"] == 0:
            self.wait_element(driver, 'table', 'date-1')
            dates = {
                    'date-1': info["monday"],
                    'date-2': info["sunday"]
                    }

            for key, val in dates.items():
                setDate = self.search_element(driver, 'table', key)
                setDate.send_keys(Keys.COMMAND, 'a')
                setDate.send_keys(Keys.BACKSPACE)
                setDate.send_keys(val)

            setDate = self.search_element(driver, 'table', 'date-2')
            setDate.send_keys(Keys.ENTER)
            sleep(7)
            self.download(driver)
        sleep(2)
        self.moveFiles()

    # login user
    def userLogin(self, driver):
        self.wait_element(driver, 'login', 'email')
        email = self.search_element(driver, 'login', 'email')
        email.send_keys(self.env('email'))
        self.search_element(driver, 'login', 'btn', click=True)
        self.wait_element(driver, 'login', 'pass')
        self.search_element(driver, 'login', 'cookies', click=True)
        self.wait_element_invisibility(driver, 'login', 'cookies')
        self.wait_element(driver, 'login', 'pass')
        password = self.search_element(driver, 'login', 'pass')
        password.send_keys(self.env('pass'))
        self.search_element(driver, 'login', 'sign-in', click=True)

        while True:
            if self.env("sf") in driver.current_url:
                break

        driver.execute_script("return document.readyState") == "complete"
        sleep(2)
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
        self._iframe(driver)
        self.download(driver)

        info = self.getWeekInfo()
        if info["weekday_index"] == 0:
            driver.get(self.env('statistics'))
            iframe = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.TAG_NAME, "iframe"))
            )
            driver.switch_to.frame(iframe)
            self.wait_element(driver, 'table', 'data', timeout=180)

            for date in info["full_week"]:
                setDate = self.search_element(driver, 'table', 'date-s')
                setDate.send_keys(Keys.COMMAND, 'a')
                setDate.send_keys(Keys.BACKSPACE)
                setDate.send_keys(date)
                self.download(driver)

        self.moveFiles()

    def gameData(self):

        # renames files
        self.modifyFiles()

        # data fetch/filtering
        def dataList(mode, stats, theFiles):
            target = Path.home() / f"Downloads/{mode}"
            for name in theFiles:

                temp = []

                file = target / name

                statsList = self.env(stats)
                envStats = statsList.replace(".csv", "")
                nameFilter = name.replace(".csv","")

                if not file.exists():
                    continue

                with open(file, newline='', encoding='utf-16') as csvfile:
                    reader = csv.reader(csvfile, delimiter='\t')
                    for i, row in enumerate(reader):
                        if i < 2 and nameFilter != envStats:
                            continue
                        if i < 1 and envStats in nameFilter:
                            continue
                        if not row:
                            continue

                        new_cols = self.filterList(row[0])
                        remaining_cols = row[1:]
                        row = new_cols + remaining_cols
                        temp.append(row)

                if nameFilter != envStats:
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

                    info = self.getWeekInfo()
                
                    def trasnfromRows(data):
                        result = []
                        removeIndex = {4, 5, 6, 7} if stats == "stats" else {4, 5, 6}
                        for row in data:
                            moveIndex = row[3] if len(row) > 3 else None
                            filterRow = [val for idx, val in enumerate(row) if idx not in removeIndex and idx != 3]
                            if moveIndex is not None:
                                filterRow.insert(0, moveIndex)
                            result.append(filterRow)
                        
                        return result
                    
                    daily = trasnfromRows(temp)
                    weekly = trasnfromRows(cleaned_temp) if info["weekday_index"] == 0 and stats == "week_stats" else ""

                # sts for stats, I aint got time to think variable names ;0
                sts = envStats if stats == "stats" else envStats.replace("(Weekly)", "")
                if sts in nameFilter:
                    updated_temp = []

                    for i, row in enumerate(temp):
                        new_row = row.copy()
                        if i != 0 and len(new_row) > 0:
                            new_row[0] = "" 
                        updated_temp.append(new_row)

                    daily = updated_temp
                    weekly = updated_temp
                    temp = updated_temp

                if info["weekday_index"] == 0 and stats == "week_stats":
                    if "Statistics (" in nameFilter:
                        weekly = temp
                        self.sheet.populateSheet(self.env("st_weekly"), f'A2', weekly)
                    else:
                        self.sheet.populateSheet(nameFilter, f'A2', weekly)
                else:
                    print(nameFilter)
                    self.sheet.populateSheet(nameFilter, f'A2', daily)

        dataList("daily", "stats", self.files)
        dataList("weekly", "week_stats", self.week_files)
        dataList("stats", "week_stats", self.weekly_stats_files)

        self.clearFolders()
