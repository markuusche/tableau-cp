import getpass
import pandas as pd
from zoneinfo import ZoneInfo
import os, re, shutil, ast, glob
from datetime import datetime, timedelta
from src.helpers.helper import Helpers

class Utils(Helpers):
    
    @staticmethod
    def readCSV(folder) -> str:
        base = os.path.expanduser("~/Downloads")
        path = os.path.join(base, folder)
        file = glob.glob(os.path.join(path, "*.csv"))
        return file
    
    @staticmethod
    def sortIndexDesc(data: list, date: str | None = None) -> list[list]:
        for row in data:
            if date:
                row.insert(0, date)
            row[4] = row[4].replace(",", "")
        
        sorted_data = sorted(data, key=lambda index: int(index[4]), reverse=True)
        for sort in sorted_data:
            sort[4] = f"{int(sort[4]):,}"
        
        return sorted_data
    
    @staticmethod
    def get_unique_path(folder, filename) -> str:
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
    
    @staticmethod
    def getWeekInfo() -> dict:
        today = datetime.now(ZoneInfo("Asia/Manila"))
        date_str = today.strftime("%Y-%m-%d")
        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
        weekday_index = date_obj.weekday()

        monday = today - timedelta(days=7)
        sunday = today - timedelta(days=1)

        full_week = [(monday + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]
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

    # rename file(s)?
    def renameFiles(self, file) -> str:
        file_names = self.env(file)
        names = ast.literal_eval(file_names) if file_names else {}
        return names
    
    def moveFiles(self, **options):
        
        downloads = os.path.expanduser("~/Downloads")
        folder = lambda folder: os.path.join(downloads, folder)
        labels = ["daily", "weekly", "stats", "games", "pages", "promo", "home_stats", "email_verification", "popUp"]

        path = {}
        for item in labels:
            path[item] = folder(item)

        for value in path.values():
            os.makedirs(value, exist_ok=True)

        files = self.renameFiles('file_names')
        file_renames = files
        
        if not options.get("game"):
            for original_name in file_renames.keys():
                source_path = os.path.join(downloads, original_name)
                daily_target_path = os.path.join(path["daily"], original_name)

                if os.path.exists(source_path):
                    if self.env("st") in original_name and os.path.exists(daily_target_path):
                        continue

                    if self.env("dg1") in original_name:
                        if options.get("gameEvent"):
                            target_folder = path["games"]
                        else:
                            target_folder = path["weekly"]
                    elif any(self.env(k) in original_name for k in ("dg", "st")):
                        if self.env("st") in original_name and options.get("month"):
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
            if os.path.isfile(filepath) and filename.startswith(tuple(self.env(key) for key in ["st", "stp", "pp", "mb", "hp", "tab", "tab1", "tab2"])):
                movePath = lambda folder: os.path.join(path[folder], filename)
                if options.get("gameEvent"):
                    destination = self.get_unique_path(path["daily"], filename)
                elif options.get("game"):
                    destination = movePath("games")
                elif options.get("page"):
                    destination = movePath("pages")
                elif options.get("promo"):
                    destination = movePath("promo")
                elif options.get("popUp"):
                    destination = movePath("popUp")
                elif options.get("homeStatistics"):
                    destination = movePath("home_stats")
                elif options.get("emailVerification"):
                    destination = movePath("email_verification")
                else:
                    destination = movePath("stats")
                    
                shutil.move(filepath, destination)

        if options.get("month"):
            monthly_folder = os.path.join(downloads, "stats")
            os.makedirs(monthly_folder, exist_ok=True)

            unnumbered_file = os.path.join(downloads, f"{self.env("stcv")}")
            if os.path.exists(unnumbered_file):
                new_path = os.path.join(monthly_folder, f"{self.env("stss")}")
                shutil.move(unnumbered_file, new_path)

    # rename the files 
    def modifyFiles(self, month: bool = False) -> None:
        base_downloads = os.path.expanduser("~/Downloads")
        folders = {
            'file_names': os.path.join(base_downloads, "daily"),
            'weekly_names': os.path.join(base_downloads, "weekly"),
            'stats_week_names': os.path.join(base_downloads, "stats"),
            'games_week_names': os.path.join(base_downloads, "games"),
            'promo_week_names': os.path.join(base_downloads, "promo"),
            'popUps': os.path.join(base_downloads, "popUp"),
        }

        def rename(folder, old_name, new_name) -> None:
            old_path = os.path.join(folder, old_name)
            if os.path.exists(old_path):
                new_path = os.path.join(folder, new_name)
                os.rename(old_path, new_path)

        if month:
            for key in list(folders.keys()):
                if key not in ["file_names", "weekly_names"]:
                    del folders[key]
        
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

    def sumEventGeneric(self, folder: str, date: str, name: str, key_cols: list[int], val_cols: list[int]) -> list[list]:
        """
        Sums all the total amount/value of all file
        """

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

    def pageData(self) -> tuple[list, list]:
        """
        Filters & separates 1 data into 2
        """
        # Sorry, for spaghetti. :3
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

    # delete daily/weekly folder
    def clearFolders(self) -> None:
        user = getpass.getuser()
        downloads = f"/Users/{user}/Downloads"
        folders_names = ["daily", "weekly", "stats", "games", "pages", "promo", "home_stats", "email_verification"]

        for folder in folders_names:
            folders = os.path.join(downloads, folder)
            if os.path.exists(folders):
                shutil.rmtree(folders)
