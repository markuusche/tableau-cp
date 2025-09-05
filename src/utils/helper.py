import yaml
import os, ast
import shutil
import getpass
import re
import glob, os
import pandas as pd
from time import sleep
from zoneinfo import ZoneInfo
from datetime import datetime, timedelta
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementNotInteractableException

class Helper:

    #locator fetch helper 
    def data(self, *keys):
        with open('src/config/locators.yaml','r') as file:
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
    
    @staticmethod
    def get_unique_path(folder, filename):
        #clean base name
        base, ext = os.path.splitext(filename)
        base = re.sub(r'\s\(\d+\)$', '', base)
        file = base + ext
        
        clean_name = file
        base, ext = os.path.splitext(clean_name)
        candidate = clean_name
        counter = 1
        while os.path.exists(os.path.join(folder, candidate)):
            candidate = f"{base} ({counter}){ext}"
            counter += 1
        return os.path.join(folder, candidate)
    
    def moveFiles(self, month: bool = False, gameEvent: bool = False, game: bool = False, page: bool = False, promo: bool = False):
        downloads = os.path.expanduser("~/Downloads")
        folder = lambda folder: os.path.join(downloads, folder)
        labels = ["daily", "weekly", "stats", "games", "pages", "promo"]

        path = {}
        for item in labels:
            path[item] = folder(item)

        for value in path.values():
            os.makedirs(value, exist_ok=True)

        files = self.renameFiles('file_names')
        file_renames = files
        
        if not game:
            for original_name in file_renames.keys():
                source_path = os.path.join(downloads, original_name)
                daily_target_path = os.path.join(path["daily"], original_name)

                if os.path.exists(source_path):
                    if self.env("st") in original_name and os.path.exists(daily_target_path):
                        continue

                    if self.env("dg1") in original_name:
                        if gameEvent:
                            target_folder = path["games"]
                        else:
                            target_folder = path["weekly"]
                    elif self.env("dg") in original_name or self.env("st") in original_name:
                        if self.env("st") in original_name and month:
                            continue
                        target_folder = path["daily"]
                    else:
                        continue

                    destination = self.get_unique_path(target_folder, original_name)
                    shutil.move(source_path, destination)
                else:
                    print(f"File not found: {original_name}")
        
        # move stats file separately to a folder
        for filename in os.listdir(downloads):
            filepath = os.path.join(downloads, filename)
            if os.path.isfile(filepath) and filename.startswith((self.env("st"), self.env("stp"), self.env("pp"))):
                movePath = lambda folder: os.path.join(path[folder], filename)
                if gameEvent:
                    destination = self.get_unique_path(path["daily"], filename)
                elif game:
                    destination = movePath("games")
                elif page:
                    destination = movePath("pages")
                elif promo:
                    destination = movePath("promo")
                else:
                    destination = movePath("stats")
                    
                shutil.move(filepath, destination)

        if month:
            monthly_folder = os.path.join(downloads, "stats")
            os.makedirs(monthly_folder, exist_ok=True)

            unnumbered_file = os.path.join(downloads, f"{self.env("stcv")}")
            if os.path.exists(unnumbered_file):
                new_path = os.path.join(monthly_folder, f"{self.env("stss")}")
                shutil.move(unnumbered_file, new_path)

    # rename the files 
    def modifyFiles(self, month=False):
        base_downloads = os.path.expanduser("~/Downloads")
        folders = {
            'file_names': os.path.join(base_downloads, "daily"),
            'weekly_names': os.path.join(base_downloads, "weekly"),
            'stats_week_names': os.path.join(base_downloads, "stats"),
            'games_week_names': os.path.join(base_downloads, "games"),
            'promo_week_names': os.path.join(base_downloads, "promo"),
        }

        def rename(folder, old_name, new_name):
            old_path = os.path.join(folder, old_name)
            if os.path.exists(old_path):
                new_path = os.path.join(folder, new_name)
                os.rename(old_path, new_path)

        if month:
            del folders["stats_week_names"]
            del folders["games_week_names"]
            del folders["promo_week_names"]
            
            keys = ["stats", "games", "promo"]
            
            for x in keys:
                path = os.path.join(base_downloads, x)

                old = os.path.join(path, f"{self.env("stcv")}")
                name = "sts" if x == "stats" else "stsg"
                new = os.path.join(path, f"{self.env(name)} (1).csv")

                if os.path.exists(old):
                    os.rename(old, new)

                for i in range(1, 33):
                    old_name = f"{self.env("st")} ({i}).csv"
                    new_name = f"{self.env(name)} ({i + 1}).csv"

                    old_path = os.path.join(path, old_name)
                    new_path = os.path.join(path, new_name)

                    if os.path.exists(old_path):
                        os.rename(old_path, new_path)
        
        for env_key, folder_path in folders.items():
            file_map = ast.literal_eval(self.env(env_key) or "{}")
            for old, new in file_map.items():
                rename(folder_path, old, new)

    def sumEventGeneric(self, folder: str, date: str, name: str, key_cols: list[int], val_cols: list[int]):

        base_downloads = os.path.expanduser("~/Downloads")
        folderPath = os.path.join(base_downloads, folder)
        csv_files = glob.glob(os.path.join(folderPath, "*.csv"))

        all_keys = {}
        for file in csv_files:
            with open(file, encoding="utf-16") as f:
                lines = f.readlines()
            for line in lines[1:]:
                parts = line.strip().split("\t")
                if len(parts) > max(key_cols):
                    key = tuple(parts[i].strip() for i in key_cols)
                    all_keys[key] = True

        total_sums = {key: {"key": key, "vals": [0, 0]} for key in all_keys.keys()}

        for file in csv_files:
            df = pd.read_csv(file, encoding="utf-16", sep="\t", header=None, engine="python")
            for _, row in df.iterrows():
                try:
                    key = tuple(str(row[i]).strip() for i in key_cols)
                    if key in total_sums:
                        val1 = float(str(row[val_cols[0]]).replace(",", ""))
                        val2 = float(str(row[val_cols[1]]).replace(",", ""))
                        total_sums[key]["vals"][0] += val1
                        total_sums[key]["vals"][1] += val2
                except (ValueError, IndexError):
                    continue

        sorted_totals = sorted(
            total_sums.items(),
            key=lambda item: item[1]["vals"][0] + item[1]["vals"][1],
            reverse=True
        )

        c = []
        for _, data in sorted_totals:
            sum1, sum2 = data["vals"]
            w = list(data["key"]) + [sum1, sum2]
            c.append(w)

        for r in c:
            category_name = name.replace('1', '').replace('()', '')
            r.insert(0, date)
            r.insert(1, category_name)

        return c

    @staticmethod
    def readCSV(folder):
        base = os.path.expanduser("~/Downloads")
        path = os.path.join(base, folder)
        file = glob.glob(os.path.join(path, "*.csv"))
        return file
    
    @staticmethod
    def sortIndexDesc(data: list, date: str | None = None):
        for row in data:
            if date:
                row.insert(0, date)
            row[4] = row[4].replace(",", "")
        
        sorted_data = sorted(data, key=lambda index: int(index[4]), reverse=True)
        for sort in sorted_data:
            sort[4] = f"{int(sort[4]):,}"
        
        return sorted_data

    def pageData(self):
        read = self.readCSV('pages')
        
        def order(filename):
            match = re.search(r"\((\d+)\)", filename)
            return int(match.group(1)) if match else -1
        
        sorted_files = sorted(read, key=order, reverse=True)

        popular = []
        others = []
        
        for p in sorted_files:
            k = [[], [], [], [], [], []]
            with open(p, encoding="utf-16") as f:
                lines = f.readlines()
            
            for line in lines[1:]: 
                row = line.strip().split("\t")
                if row[1] in self.env("homepage", True):
                    k[0].append(row)
                elif row[1] == self.env("lvsl"):
                    k[1].append(row)
                else:
                    k[2].append(row)

            k[2].extend(k[1])
            
            g = [[], []]
            
            for x in k[0]:
                if x[1] == self.env("rgs"):
                    g[0].append(x)
                else:
                    g[1].append(x)
            
            k[2].extend(g[1])
            k[2].extend(g[0])
            
            for x in k[2]:
                if x[1] == self.env("pgs"):
                    k[4].append(x)
                else:
                    k[5].append(x)
        
            popular.extend(k[4])
            others.extend(k[5])
        
        # popular sorting
        from collections import defaultdict
        sorted_data = self.sortIndexDesc(popular)
        
        #others sorting
        grouped = defaultdict(list)
        for row in others:
            category = row[1]
            grouped[category].append(row)

        sorted_result = []
        for category, rows in grouped.items():
            sorted_rows = sorted(
                rows,
                key=lambda x: int(x[4].replace(",", "")),
                reverse=True
            )
            sorted_result.extend(sorted_rows)

        others = []
        for row in sorted_result:
            others.append(row)
        
        return sorted_data, others

    # clear daily/weekly folder
    def clearFolders(self):
        user = getpass.getuser()
        downloads = f"/Users/{user}/Downloads"
        folders_names = ["daily", "weekly", "stats", "games", "pages", "promo"]

        for folder in folders_names:
            folders = os.path.join(downloads, folder)
            if os.path.exists(folders):
                shutil.rmtree(folders)
                print(f"Deleted folder: {folders}")

    # get weeks/day info
    def getWeekInfo(self):
        today = datetime.now(ZoneInfo("Asia/Manila"))
        date_str = today.strftime("%Y-%m-%d")
        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
        weekday_index = date_obj.weekday()

        monday = today - timedelta(days=7)
        sunday = today - timedelta(days=1)

        full_week = [(monday + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]

        # check if the day today is the first day of the month? stupid
        last_month_dates = []
        if date_obj.day == 1:
            first_of_last_month = (date_obj.replace(day=1) - timedelta(days=1)).replace(day=1)
            last_of_last_month = date_obj.replace(day=1) - timedelta(days=1)
            last_month_dates = [
                (first_of_last_month + timedelta(days=i)).strftime("%Y-%m-%d")
                for i in range((last_of_last_month - first_of_last_month).days + 1)
            ]

        return {
            "today": date_str,
            "weekday_index": weekday_index,
            "monday": monday.strftime("%Y-%m-%d"),
            "sunday": sunday.strftime("%Y-%m-%d"),
            "full_week": full_week,
            "last_month_dates": last_month_dates
        }
    
    # download data page
    def download(self, driver):
        driver.execute_script("return document.readyState") == "complete"
        self.wait_element(driver, 'table', 'toolbar', timeout=10)
        driver.execute_script('document.querySelector("#viz-viewer-toolbar > div:last-child #download").click();')
        self.wait_element(driver, 'table', 'download', timeout=10)
        driver.execute_script("return document.readyState") == "complete"

        # very stupid flaky 
        while True:
            try:
                self.wait_clickable(driver, 'table', 'crosstab', timeout=5)
                break
            except:
                self.wait_element(driver, 'table', 'download')
                continue
        
        driver.execute_script("return document.readyState") == "complete"
            
        # very very stupid flaky
        while True:
            try:
                self.wait_element(driver, 'table', 'pop-up', timeout=5)
                break
            except:
                try:
                    self.wait_clickable(driver, 'table', 'crosstab', timeout=5)
                    break
                except:
                    continue
        
        # another flaky guy
        while True:
            try:
                self.search_element(driver, 'table', 'csv', click=True)
                break
            except:
                continue
    
        self.search_element(driver, 'table', 'btn', click=True)
        self.wait_element_invisibility(driver, 'table', 'pop-up')
        sleep(2)
        
    def singlePage(self, driver, data, promo: bool = False):
        if not promo:
            self._iframe(driver)
        try:
            
            try:
                self.wait_element(driver, 'table', 'data', timeout=180)
            except:
                pass
            
            for date in data:
                setDate = self.search_element(driver, 'table', 'date-s')
                setDate.send_keys(Keys.COMMAND, 'a')
                setDate.send_keys(Keys.BACKSPACE)
                setDate.send_keys(date)
                self.download(driver)
        except:
            pass
        
    def _iframe(self, driver):
        iframe = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.TAG_NAME, "iframe"))
        )
        driver.switch_to.frame(iframe)
        self.wait_element(driver, 'table', 'data', timeout=10)

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
    
    def wait_element_invisibility(self, driver, *keys, absolute=False, timeout=120):
        try:
            locator = (By.CSS_SELECTOR, self.data(*keys))
            element = WebDriverWait(driver, timeout)
            if absolute:
                element.until(EC.invisibility_of_element_located(locator))
            else:  
                element.until(EC.invisibility_of_element(locator))
        except:
            print(f'\033[91m[ FAILED ] "{locator}" element still diplayed.')
    
    def wait_clickable(self, driver, *keys, timeout=60):
        locator = (By.CSS_SELECTOR, self.data(*keys))
        wait = WebDriverWait(driver, timeout)
        element = wait.until(EC.element_to_be_clickable(locator),
        message=f'\033[91m[ FAILED ] "{locator}" element was not clickable.')
        element.click()
