import csv
import os
import pyautogui
from time import sleep
from pathlib import Path
from src.utils.helper import Helper
from src.api.sheet import GoogleSheet
from selenium.webdriver.common.keys import Keys

class Tableau(Helper):

    def __init__(self):
        self.sheet = GoogleSheet()
        self.files = self.env('files', True)
        self.week_files = self.env('week_files', True)
        self.monthly_files = self.env('wkstat', True)
        self.weekly_stats_files = self.env('weekly_stats_files', True)
        self.weekly_games_files = self.env('weekly_games_files', True)
        self.promo_week = self.env('promo_weekly', True)
        self.downloads = os.path.expanduser("~/Downloads")

    # login user
    def userLogin(self, driver):
        driver.execute_script("return document.readyState") == "complete"
        self.wait_element(driver, 'login', 'user')
        user = self.search_element(driver, 'login', 'user')
        user.send_keys(self.env('email'))
        password = self.search_element(driver, 'login', 'pass')
        password.send_keys(self.env('pass'))
        self.search_element(driver, 'login', 'submit', click=True)
        self.wait_element(driver, 'dashboard', 'panel')
    
    def navigate(self, driver, monthly: bool = False, iframe: bool = False):
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
    
        self.wait_element(driver, 'table', 'date-1', timeout=120)

        if info["weekday_index"] == 0:
            inputDate(info["monday"], info["sunday"])

        if not monthly:
            self.moveFiles()
        
        if monthly:
            inputDate(info["last_month_dates"][0], info["last_month_dates"][-1])
            self.moveFiles()

    # Full game report workbook
    def gameReport(self, driver, monthly: bool = False, page: bool = False, promo: bool = False):
        self.userLogin(driver)
        info = self.getWeekInfo()

        # dashboard
        if not page and not promo:
            categories = self.env('categories', True)
            for item in categories:
                driver.get(self.env('tableau') + f"Category={item}")
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

            if info["weekday_index"] == 0:
                categories = self.env('tracking', True)
                for i, item in enumerate(categories):
                    driver.get(self.env('event') + f"页面={item}")
                    self.singlePage(driver, info["full_week"])
                    if i != 1:
                        self.moveFiles()
                    else:
                        self.moveFiles(game=True)

        if promo:
            driver.get(self.env("promo"))
            self._iframe(driver)
            self.download(driver)
            self.moveFiles(gameEvent=True)
            # for future use
            # if info["weekday_index"] == 0:
            #     self.singlePage(driver, info["full_week"], promo=True)
            #     self.moveFiles(promo=promo)

        self.moveFiles()

    def gameData(self, month: bool = False):
        
        # renames files
        self.modifyFiles(month)

        # data fetch/filtering
        def dataList(mode, stats: str, theFiles):
            target = Path.home() / f"Downloads/{mode}"
            info = self.getWeekInfo()
            for name in theFiles:

                temp = []

                file = target / name
                nameFilter = name.replace(".csv","")

                if not file.exists():
                    continue

                skip = 1 if any(keyword in nameFilter for keyword in [self.env('sts'), self.env('stsg'), self.env('pts')]) else 2
                with open(file, newline='', encoding='utf-16') as csvfile:
                    reader = csv.reader(csvfile, delimiter='\t')
                    for i, row in enumerate(reader):

                        if i < skip:
                            continue
                        
                        if not row:
                            continue

                        temp.append(row[skip:])
                        
                def insertDates(temp, data, data2):
                    for date in temp:
                        date[0] = f"{data} - {data2}"
                        
                if not month:
                    date = f"{info["monday"]} - {info["sunday"]}"
                    if info["weekday_index"] == 0 and stats in {"week_stats", "game_stats"}:
                        if "Home (" in nameFilter or "Games (" in nameFilter:
                            data = self.sumEventGeneric(mode, date, nameFilter, key_cols=[2, 3], val_cols=[4, 5])
                            env = self.env("st_weekly") if "Home (" in nameFilter else self.env("sg_weekly")
                            self.sheet.populateSheet(env, 'A2', data, event=True)
                            break
                        # for future use
                        # elif "Promo (" in nameFilter:
                        #     data = self.sumEventGeneric(mode, date, nameFilter, key_cols=[3, 4, 5], val_cols=[6, 7])
                        #     self.sheet.populateSheet(self.env("pp_weekly"), 'A2', data, event=True)
                        #     break
                        else:
                            insertDates(temp, info["monday"], info["sunday"])
                            self.sheet.populateSheet(nameFilter, 'A2', temp)
                    else:
                        # for stats only purposes condition
                        if nameFilter == self.env("sts") or nameFilter == self.env("stsg"):
                            cell = self.sheet.getCellValue(range=nameFilter, event=True) != temp[0][0]
                            
                            if cell:
                                sorted_data = self.sortIndexDesc(temp, f"{info["sunday"]}")
                                self.sheet.populateSheet(nameFilter, 'A2', sorted_data, event=True)

                        elif nameFilter == self.env("pts"):
                            self.sheet.populateSheet(nameFilter, 'A2', temp, event=True)
                        else:
                            cell = self.sheet.getCellValue(nameFilter) != temp[0][0]
                            if cell:
                                self.sheet.populateSheet(nameFilter, 'A2', temp)
                else:
                    sheet_names = nameFilter + " (Monthly)"
                    dates = info["last_month_dates"]
                    insertDates(temp, min(dates), max(dates))
                    self.sheet.populateSheet(sheet_names, 'A2', temp)

        month_or_week = self.monthly_files if month else self.weekly_stats_files
        dataList("daily", "stats", self.files)
        dataList("weekly", "week_stats", self.week_files)
        dataList("games", "game_stats", self.weekly_games_files)
        dataList("stats", "week_stats", month_or_week)
        dataList("promo", "week_stats", self.promo_week)

        self.clearFolders()
    
    def homePage(self, driver):
        self.userLogin(driver)
        driver.get(self.env("classification"))
        self._iframe(driver)
        self.download(driver)
        self.moveFiles(page=True)
        popular, others = self.pageData()
        check = self.sheet.getCellValue(self.env("pop"), event=True) != popular[0][0]
        if check:
            self.sheet.populateSheet(self.env("pop"), 'A2', popular, event=True)
            self.sheet.populateSheet(self.env("cats"), 'A2', others, event=True)

        self.clearFolders()
