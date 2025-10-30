# =====================================================================================
# =========================== [ TABLEAU DATA AUTOMATION ] =============================
# ============================= @github.com/markuusche ================================
# =============================== © 2025 - markuusche =================================
# =====================================================================================

import pytest
from src.main import Tableau
from src.utils.utils import Utils

class Test:

    data = Tableau()
    info = Utils()

    def test_daily(self, driver):
        self.data.gameReport(driver)
        self.data.gameData()
    
    def test_home(self, driver):
        self.data.gameReport(driver, page=True)
        self.data.gameData()
        
    def test_page(self, driver):
        self.data.homePage(driver)
        
    def test_promo(self, driver):
        self.data.gameReport(driver, promo=True)
        self.data.gameReport(driver, otherPromo=True)
        self.data.gameData()    
        
    def test_miniBanner(self, driver):
        self.data.gameReport(driver, miniBanner=True)
        self.data.gameData()
    
    def test_popUp(self, driver):
        self.data.gameReport(driver, popUp=True)
        self.data.gameData()
    
    # def test_homeStatistics(self, driver):
    #     self.data.gameReport(driver, homeStatistics=True)
    #     self.data.gameData()
    
    # def test_emailVerification(self, driver):
    #     self.data.gameReport(driver, emailVerification=True)
    #     self.data.gameData()
        
    def test_recentPlay(self, driver):
        self.data.gameReport(driver, recentPlay=True)
        self.data.gameData()
        
    def test_monthly(self, driver):
        if len(self.info.getWeekInfo()["last_month_dates"]) != 0:
            self.data.gameReport(driver, monthly=True)
            self.data.gameData(month=True)
        else:
            pytest.skip()
