"""Page Object Model for the E2E test suite.

Isolating element locators here (instead of scattering them across
test functions) means that if the HTML ever changes, only this file
needs updating — the tests themselves describe user intent, not CSS
selectors.
"""

from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class BasePage:
    def __init__(self, driver, base_url):
        self.driver = driver
        self.base_url = base_url

    def wait(self, timeout=5):
        return WebDriverWait(self.driver, timeout)


class HomePage(BasePage):
    def open(self):
        self.driver.get(f"{self.base_url}/")
        self.wait().until(EC.presence_of_element_located((By.CLASS_NAME, "stat-number")))
        return self

    @property
    def total_sets(self):
        # Order on the page is: sessions, exercises, sets.
        stats = self.driver.find_elements(By.CLASS_NAME, "stat-number")
        return int(stats[2].text)


class SessionsPage(BasePage):
    def open(self):
        self.driver.get(f"{self.base_url}/sessions")
        return self

    def has_session(self, name):
        return bool(
            self.driver.find_elements(
                By.XPATH, f"//span[@class='card-title' and text()='{name}']"
            )
        )

    def open_session(self, name):
        self.driver.find_element(
            By.XPATH, f"//span[@class='card-title' and text()='{name}']/ancestor::a"
        ).click()
        self.wait().until(EC.url_matches(r"/sessions/\d+$"))
        return SessionDetailPage(self.driver, self.base_url)

    def delete_session(self, name):
        card = self.driver.find_element(
            By.XPATH,
            f"//span[@class='card-title' and text()='{name}']"
            "/ancestor::div[contains(@class,'session-card')]",
        )
        # The Delete button is hidden by CSS until the card is hovered, so a
        # real user must hover first; the test does the same.
        ActionChains(self.driver).move_to_element(card).perform()
        button = card.find_element(By.CSS_SELECTOR, "button.danger-button")
        self.wait().until(lambda _: button.is_displayed())
        button.click()
        self.wait().until(EC.alert_is_present())
        self.driver.switch_to.alert.accept()
        return self


class AddSessionPage(BasePage):
    def open(self):
        self.driver.get(f"{self.base_url}/add-session")
        return self

    def create(self, name):
        self.driver.find_element(By.ID, "session_name").send_keys(name)
        self.driver.find_element(By.CSS_SELECTOR, "button.button[type='submit']").click()
        self.wait().until(EC.url_contains("/sessions"))
        return SessionsPage(self.driver, self.base_url)


class SessionDetailPage(BasePage):
    def add_exercise(self):
        self.driver.find_element(By.LINK_TEXT, "+ Add Exercise").click()
        self.wait().until(EC.url_contains("/add-exercise"))
        return AddExercisePage(self.driver, self.base_url)

    def has_exercise(self, name):
        return bool(
            self.driver.find_elements(
                By.XPATH, f"//span[@class='card-title' and text()='{name}']"
            )
        )

    def open_exercise(self, name):
        self.driver.find_element(
            By.XPATH, f"//span[@class='card-title' and text()='{name}']/ancestor::a"
        ).click()
        self.wait().until(EC.url_contains("/exercises/"))
        return ExerciseDetailPage(self.driver, self.base_url)


class AddExercisePage(BasePage):
    def create(self, name):
        self.driver.find_element(By.ID, "exercise_name").send_keys(name)
        self.driver.find_element(By.CSS_SELECTOR, "button.button[type='submit']").click()
        # After saving, the app redirects back to the session detail page.
        self.wait().until(EC.url_matches(r"/sessions/\d+$"))
        return SessionDetailPage(self.driver, self.base_url)


class ExerciseDetailPage(BasePage):
    def add_set(self):
        self.driver.find_element(By.LINK_TEXT, "+ Add Set").click()
        self.wait().until(EC.url_contains("/add-set"))
        return AddSetPage(self.driver, self.base_url)

    def has_set(self, weight_display, reps):
        xpath = (
            f"//span[@class='card-title' and text()='{weight_display} lbs']"
            "/ancestor::div[contains(@class,'set-card')]"
            f"//p[contains(text(), '{reps} rep')]"
        )
        return bool(self.driver.find_elements(By.XPATH, xpath))


class AddSetPage(BasePage):
    def create(self, weight, reps):
        self.driver.find_element(By.ID, "weight").send_keys(str(weight))
        self.driver.find_element(By.ID, "reps").send_keys(str(reps))
        self.driver.find_element(By.CSS_SELECTOR, "button.button[type='submit']").click()
        self.wait().until(EC.url_matches(r"/exercises/\d+$"))
        return ExerciseDetailPage(self.driver, self.base_url)
