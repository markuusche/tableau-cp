# =====================================================================================
# =========================== [ TABLEAU DATA AUTOMATION ] =============================
# ============================= @github.com/markuusche ================================
# =============================== © 2025 - markuusche =================================
# =====================================================================================

import csv, os
from time import sleep
from pathlib import Path
from itertools import zip_longest
from src.utils.utils import Utils
from src.utils.tools import Tools
from datetime import date, timedelta
from src.api.sheet import GoogleSheet
from selenium.webdriver.common.keys import Keys

class Tableau(Utils, Tools):

    def __init__(self):
        self.sheet = GoogleSheet()
        self.downloads = os.path.expanduser("~/Downloads")
    
    def navigate(self, driver, monthly: bool = False, iframe: bool = False) -> None:
        """
        Page navigation — helps with downloading ? :O
        """
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

        if monthly:
            inputDate(info["last_month_dates"][0], info["last_month_dates"][-1])

        self.moveFiles()

    # Full game report workbook
    def gameReport(self, driver, **options) -> None:
        """
        Downloads the data in the web
        """
        
        def getCSV(url: str):
            driver.get(url)
            self._iframe(driver)
            self.download(driver)
            self.moveFiles(gameEvent=True)

        info = self.getWeekInfo()

        # dashboard
        if all(not options.get(flag) for flag in self.env("boolKeys", True)):
            categories = self.env('categories', True)
            for item in categories:
                driver.get(self.env('tableau') + f"Category={item}")
                self.navigate(driver, monthly=options.get("monthly"))

        if options.get("page"):
            driver.get(self.env('statistics'))
            self._iframe(driver)

            if not options.get("monthly"):
                self.download(driver)
                # another data to separate
                getCSV(self.env("event") + self.env("games"))

            if info["weekday_index"] == 0:
                categories = self.env('tracking', True)
                for i, item in enumerate(categories):
                    driver.get(self.env('event') + f"页面={item}")
                    self.singlePage(driver, info["full_week"])
                    if i != 1:
                        self.moveFiles()
                    else:
                        self.moveFiles(game=True)
                        
        if options.get("miniBanner"):
           getCSV(self.env("minban"))

        if options.get("promo"):
            getCSV(self.env("promo"))
        
        if options.get("otherPromo"):
            getCSV(self.env("otherPromo"))
            
        if options.get("homeStatistics"):
            scenes = self.env("scenes", True)
            for scene in scenes:
                driver.get(self.env("rawSliders") + f"User Type={scene}")
                self._iframe(driver)
                self.wait_element(driver, 'table', 'tab')
                self.download(driver, True)

            self.moveFiles(homeStatistics=True)
        
        if options.get("emailVerification"):
            driver.get(self.env("em") + info["sunday"])
            self._iframe(driver)
            self.download(driver)
            
            for tab in ["tab-1", "tab-2"]:
                self.wait_element(driver, "table", tab)
                self.search_element(driver, "table", tab, click=True)
                self.wait_element(driver, "table", "data")
                driver.execute_script("location.reload()")
                self.download(driver)
                
            self.moveFiles(emailVerification=True)

        self.moveFiles()

    def gameData(self, month: bool = False) -> None:
        """
        Filters data and send to Google Sheet
        """
        
        # renames files
        self.modifyFiles(month)
        
        # data fetch/filtering
        def dataList(mode, stats: str, theFiles):
            target = Path.home() / f"Downloads/{mode}"
            info = self.getWeekInfo()
            scenes = self.env("scenes", True)
            run = True
            for name, scene in zip_longest(theFiles, scenes[::-1]):

                temp = []

                if not name:
                    continue

                file = target / name
                
                nameFilter = name.replace(".csv","")

                if not file.exists():
                    continue
                
                skip_rows = 1 if any(self.env(key) in nameFilter for key in self.env("skipRowsKeys", True)) else 2
                with open(file, newline='', encoding='utf-16') as csvfile:
                    reader = csv.reader(csvfile, delimiter='\t')
                    for i, row in enumerate(reader): 
                        
                        if i == 0 or not row: 
                            continue
                        
                        if scene is not None and self.env("hp") in nameFilter:
                            row.insert(8, scene)
                        
                        if nameFilter == self.env("mban") or any(self.env(key) in nameFilter for key in self.env("nameFilterKeys", True)):
                            temp.append(row)
                        else:
                            if i < skip_rows:
                                continue
                            temp.append(row[skip_rows:])

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
                        else:
                            insertDates(temp, info["monday"], info["sunday"])
                            self.sheet.populateSheet(nameFilter, 'A2', temp)
                    else:
                         match nameFilter:
                            case _ if nameFilter in [self.env("sts"), self.env("stsg")]:
                                cell = self.sheet.getCellValue(range=nameFilter, event=True) != temp[0][0]
                                if cell:
                                    sorted_data = self.sortIndexDesc(temp, f"{info["sunday"]}")
                                    self.sheet.populateSheet(nameFilter, 'A2', sorted_data, event=True)
                            
                            case _ if nameFilter in [self.env("pts"), self.env("opt"), self.env("mban")]:
                                self.sheet.populateSheet(nameFilter, 'A2', temp, event=True)
                            
                            case _ if self.env("hp") in nameFilter:
                                if run:
                                    self.sheet.clearDeleteSheet(self.env("homeStats"), 'Raw Data')
                                self.sheet.populateSheet('Raw Data', 'A2', temp, homeStats=True)
                                run = False
                                
                            case _ if any(self.env(key) in nameFilter.strip() for key in ["tab", "tab1", "tab2"]):
                                from datetime import datetime
                                sortDate = sorted(temp, key=lambda x: datetime.strptime(x[0], "%Y-%m-%d"))
                                self.sheet.populateSheet(nameFilter, 'A2', sortDate, emailVerification=True, singleData=True)
                            case _:
                                cell = self.sheet.getCellValue(nameFilter) != temp[0][0]
                                if cell:
                                    self.sheet.populateSheet(nameFilter, 'A2', temp)
                else:
                    sheet_names = nameFilter + " (Monthly)"
                    dates = info["last_month_dates"]
                    insertDates(temp, min(dates), max(dates))
                    self.sheet.populateSheet(sheet_names, 'A2', temp)

        month_or_week = self.env('wkstat', True) if month else self.env('weekly_stats_files', True)
        dataList("daily", "stats", self.env("files", True))
        dataList("weekly", "week_stats", self.env("week_files", True))
        dataList("games", "game_stats", self.env("weekly_games_files", True))
        dataList("stats", "week_stats", month_or_week)
        dataList("promo", "week_stats", self.env('promo_weekly', True))
        dataList("home_stats", "stats", self.env("homeStatsFiles", True))
        dataList("email_verification", "stats", self.env("emailFileData", True))

        self.clearFolders()
    
    def homePage(self, driver) -> None:
        """
        Gets the Home & Games data separated from main data fetching
        """

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
