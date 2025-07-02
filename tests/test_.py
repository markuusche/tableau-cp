from src.main import Tableau

class Test:

    data = Tableau()

    def test_report(self, driver):
        self.data.gameReport(driver)
        self.data.gameData()
