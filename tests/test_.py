import pytest
from src.main import Tableau
from src.utils.helper import Helper

class Test:

    data = Tableau()
    info = Helper()

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
        
    def test_monthly(self, driver):
        if len(self.info.getWeekInfo()["last_month_dates"]) != 0:
            self.data.gameReport(driver, monthly=True)
            self.data.gameData(month=True)
        else:
            pytest.skip()
