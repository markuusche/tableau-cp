
from src.main import Tableau

class Test:

    data = Tableau()

    def test_report(self, driver):
        self.data.gameReport(driver)
    
    def test_data(self):
        self.data.getData()
