import csv
import os
import pyautogui
from time import sleep
from pathlib import Path
from src.utils.helper import Helper
from src.api.sheet import GoogleSheet
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

class Tableau(Helper):

    def __init__(self):
        self.sheet = GoogleSheet()
        self.files = self.env('files', True)
        self.week_files = self.env('week_files', True)
        self.monthly_files = self.env('wkstat', True)
        self.weekly_stats_files = self.env('weekly_stats_files', True)
        self.weekly_games_files = self.env('weekly_games_files', True)
        self.downloads = os.path.expanduser("~/Downloads")

    # login user
    def userLogin(self, driver):
        driver.execute_script("return document.readyState") == "complete"
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
    
    def navigate(self, driver, monthly=False, iframe=False):
        # send date info to date text field
        info = self.getWeekInfo()
        def inputDate(dateOne, dateTwo):
            dates = {
                    'date-1': dateOne,
                    'date-2': dateTwo
                    }
            
            self.wait_element(driver, 'table', 'date-1', timeout=120)
            for key, val in dates.items():
                setDate = self.search_element(driver, 'table', key)
                setDate.send_keys(Keys.COMMAND, 'a')
                setDate.send_keys(Keys.BACKSPACE)
                setDate.send_keys(val)

            self.download(driver)
            sleep(2)

        # data table page
        if not iframe:
            self._iframe(driver)

        if not monthly:
            self.download(driver) 
    
        self.wait_element(driver, 'table', 'date-1')

        if info["weekday_index"] == 0:
            inputDate(info["monday"], info["sunday"])

        if not monthly:
            self.moveFiles()
        
        if monthly:
            inputDate(info["last_month_dates"][0], info["last_month_dates"][-1])
            self.moveFiles()

    # Full game report workbook
    def gameReport(self, driver, monthly=False, page=False):
        self.userLogin(driver)

        # dashboard
        if not page:
            categories = self.env('categories', True)
            for item in categories:
                driver.get(self.env('tableau') + f"Category={item}")
                if item == '':
                    self._iframe(driver)
                    self.wait_element(driver, 'table', 'table data')
                    table = self.search_element(driver, 'table', 'table data')
                    initial = table.get_attribute('data-datasrc')
                    pyautogui.moveTo(1426, 426)
                    pyautogui.click()
                    
                    while True:
                        try:
                            table = self.search_element(driver, 'table', 'table data')
                            current = table.get_attribute('data-datasrc')
                        except:
                            continue
                        
                        if initial == current:
                            continue
                        else:
                            break

                    self.navigate(driver, monthly=monthly, iframe=True)
                else:
                    self.navigate(driver, monthly=monthly)

        if page:
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
            if info["weekday_index"] == 0:
                categories = self.env('tracking', True)
                for i, item in enumerate(categories):
                    driver.get(self.env('event') + f"页面={item}")
                    self.singlePage(driver, info["full_week"])
                    if i != 1:
                        self.moveFiles()
                    else:
                        self.moveFiles(game=True)

        self.moveFiles()

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
                    
                # rename to oss ;00
                def update_list_index(data):
                    for index in data:
                        if len(index) > 3 and index[3] == self.env("lv"):
                            index[1] = self.env("oss")
                        
                        if index[2] == self.env("gname"):
                            index[3] = self.env("ps")

                update_list_index(temp)
                update_list_index(daily)
                update_list_index(weekly)
                update_list_index(monthly)

                if not month:
                    if info["weekday_index"] == 0 and stats in {"week_stats", "game_stats"}:
                        if "Home (" in nameFilter or "Games (" in nameFilter:
                            data = self.sumEvent(mode, f"{info["monday"]} - {info["sunday"]}", nameFilter)
                            env = self.env("st_weekly") if "Home (" in nameFilter else self.env("sg_weekly")
                            self.sheet.populateSheet(env, 'A2', data, event=True)
                            break
                        else:
                            self.sheet.populateSheet(nameFilter, 'A2', weekly)
                    else:
                        # for stats only purposes condition
                        if nameFilter == self.env("sts") or nameFilter == self.env("stsg"):
                            cell = self.sheet.getCellValue(range=nameFilter, event=True) != temp[0][0]
                            if cell:
                                self.sheet.populateSheet(nameFilter, 'A2', temp, event=True)
                        else:
                            cell = self.sheet.getCellValue(nameFilter) != daily[0][0]
                            if cell:
                                self.sheet.populateSheet(nameFilter, 'A2', daily)
                else:
                    # temporary not needed
                    if "Home (" in nameFilter:
                        # weekly = temp
                        # self.sheet.populateSheet(f"{self.env("stsmn")}", 'A2', weekly)
                        continue
                    else:
                        sheet_names = nameFilter + " (Monthly)"
                        self.sheet.populateSheet(sheet_names, 'A2', monthly)

        month_or_week = self.monthly_files if month else self.weekly_stats_files
        dataList("daily", "stats", self.files)
        dataList("weekly", "week_stats", self.week_files)
        dataList("games", "game_stats", self.weekly_games_files)
        dataList("stats", "week_stats", month_or_week)

        self.clearFolders()
    
    def homePage(self, driver):
        self.userLogin(driver)
        driver.get(self.env("classification"))
        self._iframe(driver)
        self.download(driver)
        self.moveFiles(page=True)
        a, b = self.pageData()
        check = self.sheet.getCellValue(self.env("pop"), event=True) != a[0][0]
        if check:
            self.sheet.populateSheet(self.env("pop"), 'A2', a, event=True)
            self.sheet.populateSheet(self.env("cats"), 'A2', b, event=True)

        self.clearFolders()
