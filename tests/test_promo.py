from src.main import Tableau

class Test:

    data = Tableau()

    def test_promo(self, driver):
        self.data.gameReport(driver, promo=True)
        self.data.gameData()
