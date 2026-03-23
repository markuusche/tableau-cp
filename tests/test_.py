# =====================================================================================
# =========================== [ TABLEAU DATA AUTOMATION ] =============================
# ============================= @github.com/markuusche ================================
# =============================== © 2025 - markuusche =================================
# =====================================================================================

import pytest, mergedData
from src.main import Tableau
from src.utils.utils import Utils

class Test:

    data = Tableau()
    info = Utils()

    def test_daily(self, driver):
        self.data.gameReport(driver)

    def test_home(self, driver):
        self.data.gameReport(driver, page=True)

    def test_popular(self, driver):
        self.data.homePage(driver)
        self.data.homePage(driver, cashback=True)

    def test_promo(self, driver):
        self.data.gameReport(driver, promo=True)
        self.data.gameReport(driver, otherPromo=True)

    def test_miniBanner(self, driver):
        self.data.gameReport(driver, miniBanner=True)

    def test_popUp(self, driver):
        self.data.gameReport(driver, popUp=True)
    
    def test_footer(self, driver):
        self.data.gameReport(driver, footer=True)

    def test_emailVerification(self, driver):
        self.data.gameReport(driver, emailVerification=True)

    def test_recentPlay(self, driver):
        self.data.gameReport(driver, recentPlay=True)

    def test_depositWithdraw(self, driver):
        self.data.gameReport(driver, depositWithdraw=True)

    def test_dataIndex(self, driver):
        self.data.gameReport(driver, dataIndex=True)
    
    def test_downloadStore(self, driver):
        self.data.gameReport(driver, DS=True)
    
    def test_merged_popularData(self):
        mergedData.mergedData(popular=True)
        mergedData.mergedData(manual=True)
        mergedData.mergedData(newGame=True)
        mergedData.mergedData(cashback=True)
        mergedData.mergedData()

    def test_monthly(self, driver):
        if len(self.info.getWeekInfo()["last_month_dates"]) != 0:
            self.data.gameReport(driver, monthly=True)
        else:
            pytest.skip()
