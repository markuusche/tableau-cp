import csv
import os, getpass, shutil, re
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
        self.monthly_files = self.env('wkstat', True)
        self.weekly_stats_files = self.env('weekly_stats_files', True)
        self.downloads = os.path.expanduser("~/Downloads")
    
    def _iframe(self, driver):
        iframe = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.TAG_NAME, "iframe"))
        )
        driver.switch_to.frame(iframe)
        self.wait_element(driver, 'table', 'data', timeout=30)

    # login user
    def userLogin(self, driver, month):
        self.wait_element(driver, 'login', 'email')
        email = self.search_element(driver, 'login', 'email')
        email.send_keys(self.env('email'))
        self.search_element(driver, 'login', 'btn', click=True)
        self.wait_element(driver, 'login', 'pass')
        self.search_element(driver, 'login', 'cookies', click=True)
        self.wait_element_invisibility(driver, 'login', 'cookies')
        password = self.search_element(driver, 'login', 'pass')
        password.send_keys(self.env('pass'))
        self.search_element(driver, 'login', 'sign-in', click=True)

        while True:
            if self.env("sf") in driver.current_url:
                break

        driver.execute_script("return document.readyState") == "complete"
        sleep(2)

        def sendOTP():
            actions = ActionChains(driver)
            key = self.getOTP()
            actions.send_keys(key).perform()
            actions.send_keys(Keys.ENTER).perform()

        sendOTP()
        while True:
            try:
                self.wait_element(driver, 'dashboard', 'logo')
                break
            except:
                sendOTP()
                continue
    
    def navigate(self, driver, monthly=False):
        # data table page
        self._iframe(driver)

        if not monthly:
            self.download(driver)
    
        self.wait_element(driver, 'table', 'date-1')

        # send date info to date text field
        info = self.getWeekInfo()
        def inputDate(dateOne, dateTwo):
            dates = {
                    'date-1': dateOne,
                    'date-2': dateTwo
                    }

            for key, val in dates.items():
                setDate = self.search_element(driver, 'table', key)
                setDate.send_keys(Keys.COMMAND, 'a')
                setDate.send_keys(Keys.BACKSPACE)
                setDate.send_keys(val)

            self.download(driver)
            sleep(2)

        if not monthly:
            self.moveFiles()
        
        week = info["weekday_index"] == 2

        if week: # weekly
            inputDate(info["monday"], info["sunday"])
            self.moveFiles(week=week)
        
        if monthly:
            inputDate(info["last_month_dates"][0], info["last_month_dates"][-1])
            self.moveFiles()

    # Full game report workbook
    def gameReport(self, driver, monthly=False):
        self.userLogin(driver, monthly)
        # dashboard
        categories = self.env('categories', True)
        for item in categories:
            driver.get(self.env('tableau') + f"Category={item}")
            self.navigate(driver, monthly)
        
        driver.get(self.env('statistics'))
        self._iframe(driver)

        if not monthly:
            self.download(driver)

        info = self.getWeekInfo()
        def inputDate(data):
            self.wait_element(driver, 'table', 'data', timeout=180)

            for date in data:
                setDate = self.search_element(driver, 'table', 'date-s')
                setDate.send_keys(Keys.COMMAND, 'a')
                setDate.send_keys(Keys.BACKSPACE)
                setDate.send_keys(date)
                self.download(driver)

        week = info["weekday_index"] == 2

        if week:
            inputDate(info["full_week"])

        if not monthly:
            self.moveFiles(week=week)

        if monthly:
            inputDate(info["last_month_dates"])
            self.moveFiles(month=True)

    def gameData(self, month=False):

        # renames files
        # self.modifyFiles()

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
                        filterStats = envStats.replace("Weekly", "").replace("()", "")

                        if i < 2 and filterStats not in nameFilter:
                            continue
                        if i < 1 and filterStats in nameFilter:
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
                        if not month:
                            removeIndex = {4, 5, 6, 7} if stats == "stats" else {4, 5, 6}
                        else:
                            removeIndex = {4, 5, 6}

                        for row in data:
                            moveIndex = row[3] if len(row) > 3 else None
                            filterRow = [val for idx, val in enumerate(row) if idx not in removeIndex and idx != 3]
                            if moveIndex is not None:
                                filterRow.insert(0, moveIndex)
                            result.append(filterRow)
                        
                        return result
                    
                    daily = trasnfromRows(temp)
                    weekly = trasnfromRows(cleaned_temp) if info["weekday_index"] == 2 and stats == "week_stats" else ""
                    monthly = weekly = trasnfromRows(cleaned_temp)

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

                if not month:
                    if info["weekday_index"] == 2 and stats == "week_stats":
                        if "Statistics (" in nameFilter:
                            weekly = temp
                            self.sheet.populateSheet(self.env("st_weekly"), f'A2', weekly)
                        else:
                            self.sheet.populateSheet(nameFilter, f'A2', weekly)
                    else:
                        self.sheet.populateSheet(nameFilter, f'A2', daily)
                else:
                    if "Statistics (" in nameFilter:
                        weekly = temp
                        self.sheet.populateSheet("Statistics (Monthly)", f'A2', weekly)
                    else:
                        sheet_names = nameFilter + " (Monthly)"
                        self.sheet.populateSheet(sheet_names, f'A2', monthly)

        mnonthly_files = self.monthly_files if month else self.weekly_stats_files
        dataList("daily", "stats", self.files)
        dataList("weekly", "week_stats", self.week_files)
        dataList("stats", "week_stats", mnonthly_files)

        # self.clearFolders()
