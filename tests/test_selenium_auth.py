"""
Selenium integration tests for the login / auth flow.

Architecture note
-----------------
TestingConfig uses sqlite:///:memory:, which can't be shared across OS processes.
SeleniumTestConfig below points at a real file on disk so the Flask server
subprocess and the test-setup code in the parent process both see the same data.
The module-level _run_flask_server() function is required by multiprocessing on
Windows (spawn), which cannot pickle bound methods or lambdas.
"""

import multiprocessing
import os
import time
import unittest
from unittest import TestCase

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from app import create_app, db
from app.config import TestingConfig
from app.models import User

LOCAL_HOST = "http://localhost:5000/"

# Absolute path so the subprocess can locate the file regardless of cwd
TEST_DB_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "selenium_test.db")
)


class SeleniumTestConfig(TestingConfig):
    """File-backed SQLite so parent and server subprocess share the same rows."""
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{TEST_DB_PATH}"
    WTF_CSRF_ENABLED = False


# ---------------------------------------------------------------------------
# Module-level helper — must NOT be a lambda or nested function so that
# multiprocessing can pickle it when spawning on Windows.
# ---------------------------------------------------------------------------
def _run_flask_server():
    """Start the Flask dev server inside the subprocess."""
    app = create_app(SeleniumTestConfig)
    app.run(port=5000, use_reloader=False, debug=False)


def _add_test_user():
    """Seed one known account that login tests can use."""
    user = User(username="seluser", display_name="Sel User", avatar="av1")
    user.set_password("Test@1234")
    db.session.add(user)
    db.session.commit()


# ---------------------------------------------------------------------------
# Test class
# ---------------------------------------------------------------------------
class SeleniumLoginTests(TestCase):

    def setUp(self):
        # Remove any stale DB file from a previous run
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)

        # Set up the DB in the parent process — the server subprocess will
        # read from the same file.
        self.testApp = create_app(SeleniumTestConfig)
        self.app_context = self.testApp.app_context()
        self.app_context.push()
        db.create_all()
        _add_test_user()

        # Start Flask server in a subprocess so tearDown can terminate() it
        self.server = multiprocessing.Process(target=_run_flask_server)
        self.server.start()
        time.sleep(1)  # Give the server a moment to bind port 5000

        # Headless Chrome
        options = webdriver.ChromeOptions()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        self.driver = webdriver.Chrome(options=options)
        self.driver.get(LOCAL_HOST)

    def tearDown(self):
        self.server.terminate()
        self.driver.quit()
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)

    # -----------------------------------------------------------------------
    # Tests
    # -----------------------------------------------------------------------

    def test_login_page_loads(self):
        """Home page renders username and password fields."""
        wait = WebDriverWait(self.driver, 5)
        username_field = wait.until(
            EC.presence_of_element_located((By.NAME, "username"))
        )
        password_field = self.driver.find_element(By.NAME, "password")
        self.assertTrue(username_field.is_displayed())
        self.assertTrue(password_field.is_displayed())

    def test_login_success_redirects_to_stages(self):
        """Valid credentials redirect the user to the game selection page."""
        wait = WebDriverWait(self.driver, 5)
        wait.until(
            EC.presence_of_element_located((By.NAME, "username"))
        ).send_keys("seluser")
        self.driver.find_element(By.NAME, "password").send_keys("Test@1234")
        self.driver.find_element(By.CSS_SELECTOR, "[type=submit]").click()
        wait.until(EC.url_contains("/stages"))
        self.assertIn("/stages", self.driver.current_url)

    def test_wrong_password_shows_error(self):
        """An incorrect password keeps the user on the login page with an alert."""
        wait = WebDriverWait(self.driver, 5)
        wait.until(
            EC.presence_of_element_located((By.NAME, "username"))
        ).send_keys("seluser")
        self.driver.find_element(By.NAME, "password").send_keys("WrongPass999!")
        self.driver.find_element(By.CSS_SELECTOR, "[type=submit]").click()
        error = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "alert")))
        self.assertIn("Invalid username or password", error.text)

    def test_nonexistent_username_shows_error(self):
        """An unknown username keeps the user on the login page with an alert."""
        wait = WebDriverWait(self.driver, 5)
        wait.until(
            EC.presence_of_element_located((By.NAME, "username"))
        ).send_keys("ghost_user")
        self.driver.find_element(By.NAME, "password").send_keys("Test@1234")
        self.driver.find_element(By.CSS_SELECTOR, "[type=submit]").click()
        error = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "alert")))
        self.assertIn("Invalid username or password", error.text)

    def test_logout_returns_to_login_page(self):
        """After logging out the user lands back on the home/login page."""
        wait = WebDriverWait(self.driver, 5)
        # Log in first
        wait.until(
            EC.presence_of_element_located((By.NAME, "username"))
        ).send_keys("seluser")
        self.driver.find_element(By.NAME, "password").send_keys("Test@1234")
        self.driver.find_element(By.CSS_SELECTOR, "[type=submit]").click()
        wait.until(EC.url_contains("/stages"))
        # Navigate to /logout
        self.driver.get(LOCAL_HOST + "logout")
        wait.until(EC.url_to_be(LOCAL_HOST))
        self.assertEqual(self.driver.current_url, LOCAL_HOST)

    def test_signup_page_loads(self):
        """Signup page renders all three required form fields."""
        self.driver.get(LOCAL_HOST + "signup")
        wait = WebDriverWait(self.driver, 5)
        wait.until(EC.presence_of_element_located((By.NAME, "username")))
        self.assertTrue(
            self.driver.find_element(By.NAME, "password").is_displayed()
        )
        self.assertTrue(
            self.driver.find_element(By.NAME, "confirm_password").is_displayed()
        )

    def test_signup_new_user_redirects_to_customisation(self):
        """A valid new-account submission lands on the customisation page."""
        self.driver.get(LOCAL_HOST + "signup")
        wait = WebDriverWait(self.driver, 5)
        wait.until(
            EC.presence_of_element_located((By.NAME, "username"))
        ).send_keys("brandnewuser")
        self.driver.find_element(By.NAME, "password").send_keys("Test@1234")
        self.driver.find_element(By.NAME, "confirm_password").send_keys("Test@1234")
        self.driver.find_element(By.CSS_SELECTOR, "[type=submit]").click()
        wait.until(EC.url_contains("/customisation"))
        self.assertIn("/customisation", self.driver.current_url)

    def test_forgot_password_link_navigates(self):
        """Clicking the 'Forgot password?' link reaches the forgot-password page."""
        wait = WebDriverWait(self.driver, 5)
        wait.until(
            EC.presence_of_element_located(
                (By.PARTIAL_LINK_TEXT, "Forgot password")
            )
        ).click()
        wait.until(EC.url_contains("/forgot-password"))
        self.assertIn("/forgot-password", self.driver.current_url)


if __name__ == "__main__":
    unittest.main()
