import pytest
from src.main import Tableau
from src.utils.helper import Helper

class Test:

    info = Helper()
    data = Tableau()

    def test_monthly(self, driver):
        if len(self.info.getWeekInfo()["last_month_dates"]) != 0:
            self.data.gameReport(driver, monthly=True)
            self.data.gameData(month=True)
        else:
            pytest.skip()
