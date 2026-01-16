# =====================================================================================
# =========================== [ TABLEAU DATA AUTOMATION ] =============================
# ============================= @github.com/markuusche ================================
# =============================== © 2025 - markuusche =================================
# =====================================================================================

import csv, os
from time import sleep
from pathlib import Path
from src.utils.utils import Utils
from src.utils.tools import Tools
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
        
        def getCSV(url: str, dataIndex: bool = False, selector: str = 'data'):
            driver.get(url)
            self._iframe(driver, selector=selector)
            self.download(driver, dataIndex=dataIndex)
            self.moveFiles(gameEvent=True)

        info = self.getWeekInfo()

        # all game data
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
                        
        os_envs = ['miniBanner', 'promo', 'otherPromo', 'recentPlay', 'dataIndex']
        for env in os_envs:
            if options.get(env):
                if env == 'dataIndex':
                    getCSV(self.env(env) + info['sunday'], dataIndex=True, selector='index table')
                else:
                    getCSV(self.env(env))
        
        if options.get("popUp") or options.get("depositWithdraw"):
            key_list = "advertisement" if options.get("popUp") else "dp"
            keys = self.env(key_list, True)

            for key in keys:
                driver.get(self.env("popUp") + key)
                self._iframe(driver)
                self.download(driver)

            self.moveFiles(popUp=True)
            
        # currently using CPE not pacman anymore ;)
        if options.get("pacMan"):
            driver.get(self.env("pac") + info["sunday"])
            self._iframe(driver)
            self.download(driver)
            self.moveFiles(pacMan=True)
        
        if options.get("emailVerification"):
            driver.get(self.env("em") + info["sunday"])
            self._iframe(driver)
            self.download(driver)
            
            self.wait_element(driver, "table", "tab-2")
            self.search_element(driver, "table", "tab-2", click=True)
            self.wait_element(driver, "table", "data", timeout=180)
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
        def dataList(mode, stats: str, theFiles, em: bool = False):
            target = Path.home() / f"Downloads/{mode}"
            info = self.getWeekInfo()

            for name in theFiles:

                temp = []

                if not name:
                    continue

                file = target / name
                
                nameFilter = name.replace(".csv","")

                if not file.exists():
                    continue

                skip_rows = 1 if any(self.env(key) in nameFilter for key in self.env("skipRowsKeys", True)) else 2
                with open(file, newline='', encoding='utf-16') as csvfile:
                    if not em:
                        reader = csv.reader(csvfile, delimiter='\t')
                        for i, row in enumerate(reader): 
                            
                            if i == 0 or not row: 
                                continue
                            
                            if nameFilter == self.env("mban") or any(self.env(key) in nameFilter for key in self.env("nameFilterKeys", True)):
                                temp.append(row)
                            else:
                                if i < skip_rows:
                                    continue
                                temp.append(row[skip_rows:])
                    else:
                        reader = csv.DictReader(csvfile, delimiter='\t')
                        headers = reader.fieldnames
                        cols = self.env('cols', True)

                        rows = list(reader)
                        rows = rows[1:] if len(rows) > 1 else []

                        data = [] 

                        for column in cols:
                            if column in headers:
                                col_data = [row.get(column, '').strip() for row in rows]
                                data.extend(col_data)
                            else:
                                data.append('')
                                
                        temp = [data]

                if not month:
                    date = f"{info["monday"]} - {info["sunday"]}"
                    if info["weekday_index"] == 0 and stats in {"week_stats", "game_stats"}:
                        if "Home (" in nameFilter or "Games (" in nameFilter:
                            data = self.sumEventGeneric(mode, date, nameFilter, key_cols=[2, 3], val_cols=[4, 5])
                            env = self.env("st_weekly") if "Home (" in nameFilter else self.env("sg_weekly")
                            self.sheet.populateSheet(env, data, event=True)
                            break
                        else:
                            temp_data = [[date] + idx[1:] for idx in temp]
                            self.sheet.populateSheet(nameFilter, temp_data)
                    else:
                        match nameFilter:
                            case _ if nameFilter in [self.env("sts"), self.env("stsg")]:
                                sorted_data = self.sortIndexDesc(data=temp)
                                self.sheet.populateSheet(nameFilter, sorted_data, event=True)
                            
                            case _ if nameFilter in [self.env("pts"), self.env("opt"), self.env("mban")]:
                                self.sheet.populateSheet(nameFilter, temp, event=True)
                                
                            case _ if nameFilter == self.env("rp"):
                                recentPlaySort = sorted(temp, key=lambda row: int(row[5].replace(',', '')), reverse=True)
                                total = [item for item in recentPlaySort if "Total" in item]   
                                self.sheet.populateSheet(self.env("t20"), total[:20], popular=True)
                                
                            case _ if nameFilter in [self.env("pup"), self.env("cpup")]:
                                if "Deposit" in temp[0][2] or "Withdraw" in temp[0][2]:
                                    for item in temp:
                                        item[2] = item[2].replace(self.env("sts") + ":", "")
                                    self.sheet.populateSheet(self.env("dpname"), temp, dataIndex=True, no_cell_check=True)
                                else:
                                    self.sheet.populateSheet(self.env("pup"), temp, event=True, no_cell_check=True)
                                                            
                            case _ if nameFilter == self.env("pacs"):
                                pac = [item for item in temp if "Total" in item]   
                                self.sheet.populateSheet(nameFilter, pac, event=True)
                                self.sheet.populateSheet(self.env("pactotal"), pac, popular=True)
                                
                            case _ if any(self.env(key) in nameFilter.strip() for key in ["tab1", "tab2"]):
                                self.sheet.populateSheet(nameFilter, temp, emailVerification=True, singleData=True)
                                
                            case _ if self.env("indx") in nameFilter:
                                temp.pop(0)
                                raw = []
                                for item in temp:
                                    raw.append(item[1])
                                raw.insert(0, info["sunday"])
                                data = [raw]
                                
                                self.sheet.populateSheet(nameFilter, data, dataIndex=True)

                                for row in data:
                                    if info["sunday"] in row:
                                        data_result = int(row[2].replace(",","")) - int(row[3].replace(",",""))
                                        withdraw_data = [[row[14], f"{data_result:,}"]]
                                        dp_data = [[row[13], row[2]]]
                                
                                common_args = dict(
                                    dataIndex=True,
                                    no_cell_check=True,
                                    no_cell_overwrite=True
                                )

                                for data, cell in [(withdraw_data, "F3"), (dp_data, "F2")]:
                                    self.sheet.populateSheet(self.env("dpname"), data, cell=cell, **common_args)

                            case _:
                                self.sheet.populateSheet(nameFilter, temp)
                else:
                    sheet_names = nameFilter + " (Monthly)"
                    dates = info["last_month_dates"]
                    temp_data = [[f"{min(dates)} - {max(dates)}"] + idx[1:] for idx in temp]
                    self.sheet.populateSheet(sheet_names, temp_data)

        month_or_week = self.env('wkstat', True) if month else self.env('weekly_stats_files', True)
        dataList("daily", "stats", self.env("files", True))
        dataList("weekly", "week_stats", self.env("week_files", True))
        dataList("games", "game_stats", self.env("weekly_games_files", True))
        dataList("stats", "week_stats", month_or_week)
        dataList("promo", "week_stats", self.env('promo_weekly', True))
        dataList("email_verification", "stats", self.env("emailFileData", True), em=True)
        dataList("popUp", "stats", self.env("popUpNames", True))
        dataList("pacMan", "stats", self.env("pacNames", True))

        self.clearFolders()
    
    def homePage(self, driver) -> None:
        """
        Gets the Home & Games data separated from main data fetching
        """
        info = self.getWeekInfo()
        driver.get(self.env("classification") + info["sunday"])
        self._iframe(driver)
        self.download(driver)
        self.moveFiles(page=True)
        popular, others, qrqm, manual = self.pageData()
        pinoy = [row for row in others if self.env("pnyslts") in row]
        self.sheet.populateSheet(self.env("pop"), popular, event=True)
        self.sheet.populateSheet(self.env("cats"), others, event=True)
        self.sheet.populateSheet(self.env("qrqm"), qrqm, popular=True)
        self.sheet.populateSheet(self.env("manual"), manual, popular=True)
        self.sheet.populateSheet(self.env("pny"), pinoy, popular=True)
        
        self.clearFolders()
