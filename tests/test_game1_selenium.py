import multiprocessing
import os
import tempfile
import time
import unittest

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from app import create_app
from app.config import TestingConfig
from app.models import User, db


PORT = 5051
BASE_URL = f'http://127.0.0.1:{PORT}'


def _run_server(db_path, port):
    from app import create_app as _create_app
    from app.config import TestingConfig as _TestingConfig

    class _Cfg(_TestingConfig):
        SQLALCHEMY_DATABASE_URI = f'sqlite:///{db_path}'

    child_app = _create_app(_Cfg)
    child_app.run(port=port, use_reloader=False)


class Game1SeleniumTests(unittest.TestCase):
    def setUp(self):
        db_fd, self.db_path = tempfile.mkstemp(suffix='.db')
        os.close(db_fd)

        class _Cfg(TestingConfig):
            SQLALCHEMY_DATABASE_URI = f'sqlite:///{self.db_path}'

        self.testApp = create_app(_Cfg)
        self.app_context = self.testApp.app_context()
        self.app_context.push()
        db.create_all()

        self.user = User(username='seleniumWilson', display_name='Selenium Wilson')
        self.user.set_password('password1')
        db.session.add(self.user)
        db.session.commit()

        self.server_thread = multiprocessing.Process(
            target=_run_server,
            args=(self.db_path, PORT),
        )
        self.server_thread.start()
        time.sleep(1)

        options = webdriver.ChromeOptions()
        options.add_argument('--headless=new')
        options.add_argument('--window-size=1280,900')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-gpu')
        self.driver = webdriver.Chrome(options=options)
        self.driver.get(BASE_URL)

    def tearDown(self):
        self.server_thread.terminate()
        self.server_thread.join()
        self.driver.close()
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        try:
            os.unlink(self.db_path)
        except (PermissionError, FileNotFoundError):
            pass

    def _login(self):
        self.driver.get(f'{BASE_URL}/')
        WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.NAME, 'username'))
        )
        self.driver.find_element(By.NAME, 'username').send_keys('seleniumWilson')
        self.driver.find_element(By.NAME, 'password').send_keys('password1')
        self.driver.find_element(By.TAG_NAME, 'form').submit()
        WebDriverWait(self.driver, 5).until(EC.url_contains('/stages'))

    def test_anon_redirects_to_login(self):
        self.driver.get(f'{BASE_URL}/game1')
        WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.NAME, 'username'))
        )
        self.assertIn('next=', self.driver.current_url)

    def test_game1_renders_page(self):
        self._login()
        self.driver.get(f'{BASE_URL}/game1')

        WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.ID, 'start-button'))
        )

        body_text = self.driver.find_element(By.TAG_NAME, 'body').text
        self.assertIn("Where's Wilson", body_text)
        wilson = self.driver.find_element(By.ID, 'wilson')
        self.assertEqual(wilson.get_attribute('id'), 'wilson')

    def test_start_and_click_wilson_shows_result(self):
        self._login()
        self.driver.get(f'{BASE_URL}/game1')

        start = WebDriverWait(self.driver, 5).until(
            EC.element_to_be_clickable((By.ID, 'start-button'))
        )
        start.click()

        wilson = WebDriverWait(self.driver, 5).until(
            EC.element_to_be_clickable((By.ID, 'wilson'))
        )
        wilson.click()

        result = WebDriverWait(self.driver, 5).until(
            EC.visibility_of_element_located((By.ID, 'resultOverlay'))
        )
        self.assertTrue(result.is_displayed())
        self.assertIn('You found Wilson', self.driver.find_element(By.ID, 'result-message').text)


if __name__ == '__main__':
    unittest.main()