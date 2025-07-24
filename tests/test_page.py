from src.main import Tableau

class Test:

    data = Tableau()

    def test_page(self, driver):
        self.data.homePage(driver)
