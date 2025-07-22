import csv
import os
from pathlib import Path
from time import sleep
from pathlib import Path
from src.utils.helper import Helper
from src.api.sheet import GoogleSheet
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementNotInteractableException

class Tableau(Helper):

    def __init__(self):
        self.sheet = GoogleSheet()
        self.files = self.env('files', True)
        self.week_files = self.env('week_files', True)
        self.monthly_files = self.env('wkstat', True)
        self.weekly_stats_files = self.env('weekly_stats_files', True)
        self.weekly_games_files = self.env('weekly_games_files', True)
        self.downloads = os.path.expanduser("~/Downloads")
    
    def _iframe(self, driver):
        iframe = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.TAG_NAME, "iframe"))
        )
        driver.switch_to.frame(iframe)
        self.wait_element(driver, 'table', 'data', timeout=180)

    # login user
    def userLogin(self, driver):
        self.wait_element(driver, 'login', 'email')
        email = self.search_element(driver, 'login', 'email')
        email.send_keys(self.env('email'))
        self.search_element(driver, 'login', 'btn', click=True)
        self.wait_element(driver, 'login', 'pass')
        try:
            self.search_element(driver, 'login', 'cookies', click=True)
            self.wait_element_invisibility(driver, 'login', 'cookies')
        except:
            pass
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

        if info["weekday_index"] == 0:
            inputDate(info["monday"], info["sunday"])

        if not monthly:
            self.moveFiles()
        
        if monthly:
            inputDate(info["last_month_dates"][0], info["last_month_dates"][-1])
            self.moveFiles()

    # Full game report workbook
    def gameReport(self, driver, monthly=False):
        self.userLogin(driver)

        # dashboard
        categories = self.env('categories', True)
        for item in categories:
            driver.get(self.env('tableau') + f"Category={item}")
            self.navigate(driver, monthly)
        
        driver.get(self.env('statistics'))
        self._iframe(driver)

        if not monthly:
            self.download(driver)
            
            # another data to separate
            driver.get(self.env("event") + self.env("games"))
            self._iframe(driver)
            self.download(driver)
            self.moveFiles(gameEvent=True)

        info = self.getWeekInfo()
        def inputDate(data):
            try:
                self._iframe(driver)
                self.wait_element(driver, 'table', 'data', timeout=180)

                for date in data:
                    setDate = self.search_element(driver, 'table', 'date-s')
                    setDate.send_keys(Keys.COMMAND, 'a')
                    setDate.send_keys(Keys.BACKSPACE)
                    setDate.send_keys(date)
                    self.download(driver)
            except ElementNotInteractableException:
                pass
        
        if info["weekday_index"] == 0:
            categories = self.env('tracking', True)
            for i, item in enumerate(categories):
                driver.get(self.env('event') + f"页面={item}")
                inputDate(info["full_week"])
                if i != 1:
                    self.moveFiles()
                else:
                    self.moveFiles(game=True)

        self.moveFiles()

        if monthly:
            inputDate(info["last_month_dates"])
            self.moveFiles(monthly)

    def gameData(self, month=False):

        # renames files
        self.modifyFiles(month)

        # data fetch/filtering
        def dataList(mode, stats, theFiles):
            target = Path.home() / f"Downloads/{mode}"
            info = self.getWeekInfo()
            for name in theFiles:

                temp = []
                monthly = []

                file = target / name

                statsList = self.env(stats)
                envStats = statsList.replace(".csv", "")
                nameFilter = name.replace(".csv","")

                if not file.exists():
                    continue

                skip = 1 if any(keyword in nameFilter for keyword in [self.env('sts'), self.env('stsg')]) else 2
                with open(file, newline='', encoding='utf-16') as csvfile:
                    reader = csv.reader(csvfile, delimiter='\t')
                    for i, row in enumerate(reader):

                        if i < skip:
                            continue
                        if not row:
                            continue

                        new_cols = self.filterList(row[0])
                        remaining_cols = row[1:]
                        row = new_cols + remaining_cols
                        temp.append(row)

                if nameFilter != envStats or nameFilter != self.env("stsg"):
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
                    weekly = trasnfromRows(cleaned_temp) if info["weekday_index"] == 0 and stats in {"week_stats", "game_stats"} else ""
                    monthly = trasnfromRows(cleaned_temp)

                def filter_rows(temp: list[list]) -> list[list]:
                    updated_temp = []
                    for i, row in enumerate(temp):
                        new_row = row.copy()
                        if i != 0 and new_row:
                            new_row[0] = ""
                        updated_temp.append(new_row)
                    return updated_temp

                # sts for stats, I aint got time to think variable names ;0
                if stats == "stats":
                    sts = envStats
                elif nameFilter == self.env("stsg"):
                    sts = self.env("stsg")
                else:
                    sts = envStats.replace("(Weekly)", "")
                    
                if sts in nameFilter:
                    daily = filter_rows(temp)
                    weekly =  filter_rows(temp)
                    temp =  filter_rows(temp)

                # rename to oss ;00
                def update_list_index(data):
                    for index in data:
                        if len(index) > 3 and index[3] == self.env("lv"):
                            index[1] = self.env("oss")

                update_list_index(temp)
                update_list_index(daily)
                update_list_index(weekly)
                update_list_index(monthly)

                if not month:
                    if info["weekday_index"] == 0 and stats in {"week_stats", "game_stats"}:
                        if "Home (" in nameFilter:
                            data = self.sumEvent(mode, f"{info["monday"]} - {info["sunday"]}")
                            self.sheet.populateSheet(self.env("st_weekly"), 'A2', data, event=True)
                            break
                        elif "Games (" in nameFilter:
                            data = self.sumEvent(mode, f"{info["monday"]} - {info["sunday"]}")
                            self.sheet.populateSheet(self.env("sg_weekly"), 'A2', data, event=True)
                            break
                        else:
                            self.sheet.populateSheet(nameFilter, 'A2', weekly)
                    else:
                        # for stats only purposes condition
                        if nameFilter == self.env("sts"):
                            cell = self.sheet.getCellValue(range=nameFilter, event=True) != daily[0][0]
                            if cell:
                                self.sheet.populateSheet(nameFilter, 'A2', daily, event=True)
                        elif nameFilter == self.env("stsg"):
                            temp = filter_rows(temp)
                            cell = self.sheet.getCellValue(range=nameFilter, event=True) != temp[0][0]
                            if cell:
                                self.sheet.populateSheet(nameFilter, 'A2', temp, event=True)
                        else:
                            self.sheet.populateSheet(nameFilter, 'A2', daily)
                else:
                    if "Home (" in nameFilter:
                        weekly = temp
                        self.sheet.populateSheet(f"{self.env("stsmn")}", 'A2', weekly)
                    else:
                        sheet_names = nameFilter + " (Monthly)"
                        self.sheet.populateSheet(sheet_names, 'A2', monthly)

        month_or_week = self.monthly_files if month else self.weekly_stats_files
        dataList("daily", "stats", self.files)
        dataList("weekly", "week_stats", self.week_files)
        dataList("games", "game_stats", self.weekly_games_files)
        dataList("stats", "week_stats", month_or_week)

        self.clearFolders()
