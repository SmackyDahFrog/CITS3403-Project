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
from app.models import KaiRun, User, db


PORT = 5050
BASE_URL = f'http://127.0.0.1:{PORT}'


def _run_server(db_path, port):
    # top-level target so multiprocessing.Process on windows-spawn can pickle and re-import it.
    # the child interpreter rebuilds the app pointed at the same sqlite file the parent seeded.
    from app import create_app as _create_app
    from app.config import TestingConfig as _TestingConfig

    class _Cfg(_TestingConfig):
        SQLALCHEMY_DATABASE_URI = f'sqlite:///{db_path}'

    child_app = _create_app(_Cfg)
    child_app.run(port=port, use_reloader=False)


class KaiSeleniumTests(unittest.TestCase):
    # follows the lecture 13 selenium pattern: per-test setUp/tearDown, server in its own
    # process, headless chrome via ChromeOptions. selenium 4 fetches the driver itself.

    def setUp(self):
        # fresh sqlite file per test so the parent test process (which seeds the db) and
        # the child flask server process read the same rows. in-memory sqlite is per-connection
        # so it can't be shared across processes
        db_fd, self.db_path = tempfile.mkstemp(suffix='.db')
        os.close(db_fd)

        # bespoke config that points at this test's tempfile
        class _Cfg(TestingConfig):
            SQLALCHEMY_DATABASE_URI = f'sqlite:///{self.db_path}'

        self.testApp = create_app(_Cfg)
        self.app_context = self.testApp.app_context()
        self.app_context.push()
        db.create_all()

        # seed the logged-in user and a rival who'll show up on the top-3 leaderboard
        self.user = User(username='seleniumKai', display_name='Selenium Kai')
        self.user.set_password('password1')
        db.session.add(self.user)
        top = User(username='topPlayer', display_name='Top Player')
        top.set_password('password1')
        db.session.add(top)
        db.session.commit()
        db.session.add(KaiRun(user_id=top.id, time_ms=99999, avg_eat_ms=400, eat_count=10))
        db.session.commit()

        # start the flask server in its own process, sleep briefly so it's actually listening
        self.server_thread = multiprocessing.Process(
            target=_run_server, args=(self.db_path, PORT)
        )
        self.server_thread.start()
        time.sleep(1)

        # headless chrome, wide window so the canvas isn't hidden by the kai.css media query
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
        # on windows the daemon server thread can still hold the file briefly, swallow the error
        try:
            os.unlink(self.db_path)
        except (PermissionError, FileNotFoundError):
            pass

    # helper, log in by submitting the real form so flask-login sets the session cookie
    def _login(self):
        self.driver.get(f'{BASE_URL}/')
        WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.NAME, 'username'))
        )
        self.driver.find_element(By.NAME, 'username').send_keys('seleniumKai')
        self.driver.find_element(By.NAME, 'password').send_keys('password1')
        self.driver.find_element(By.TAG_NAME, 'form').submit()
        WebDriverWait(self.driver, 5).until(EC.url_contains('/stages'))

    # 1) hitting the game page logged out should bounce you to the login screen
    def test_anon_redirects_to_login(self):
        self.driver.get(f'{BASE_URL}/play/kai')
        WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.NAME, 'username'))
        )
        # flask-login appends ?next=... so url ends up at /?next=/play/kai
        self.assertIn('next=', self.driver.current_url)

    # 2) logged in, the page should render the canvas and the Snack-Time heading
    def test_play_kai_renders_canvas(self):
        self._login()
        self.driver.get(f'{BASE_URL}/play/kai')
        WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.ID, 'kaiCanvas')))
        self.assertIn('Snack-Time', self.driver.page_source)
        self.assertTrue(self.driver.find_element(By.ID, 'restartBtn').is_displayed())

    # 3) the restart button is clickable and the page doesn't fall over after we hit it
    def test_restart_button_clickable(self):
        self._login()
        self.driver.get(f'{BASE_URL}/play/kai')
        WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.ID, 'restartBtn')))
        btn = self.driver.find_element(By.ID, 'restartBtn')
        # button can sit just below the headless viewport, use a js click so chromedriver
        # doesn't bail on coord-based intercept checks when something else is overlapping
        self.driver.execute_script("arguments[0].click();", btn)
        self.assertTrue(self.driver.find_element(By.ID, 'kaiCanvas').is_displayed())

    # 4) sound dropdown change should save into localStorage so it persists across reloads
    def test_sound_dropdown_persists_in_local_storage(self):
        self._login()
        self.driver.get(f'{BASE_URL}/play/kai')
        WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.ID, 'soundSelect')))
        # set the value and fire change, dodges click-intercepted issues with the dropdown
        self.driver.execute_script(
            "var s=document.getElementById('soundSelect');"
            "s.value='Moshi';"
            "s.dispatchEvent(new Event('change'));"
        )
        stored = self.driver.execute_script("return localStorage.getItem('kai-sound');")
        self.assertEqual(stored, 'Moshi')
        # reload, the script should rehydrate the saved choice into the dropdown
        self.driver.refresh()
        WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.ID, 'soundSelect')))
        after_reload = self.driver.execute_script(
            "return document.getElementById('soundSelect').value;"
        )
        self.assertEqual(after_reload, 'Moshi')

    # 5) the back to stages link takes you back to /stages
    def test_back_to_stages_link(self):
        self._login()
        self.driver.get(f'{BASE_URL}/play/kai')
        WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.ID, 'kaiCanvas')))
        back = self.driver.find_element(By.XPATH, "//a[contains(@href, '/stages')]")
        # link sits below the canvas, scroll it into view so it isn't covered by anything
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", back)
        back.click()
        WebDriverWait(self.driver, 5).until(EC.url_contains('/stages'))
        self.assertIn('/stages', self.driver.current_url)

    # 6) the leaderboard renders our seeded top player's name, proves server-rendered data
    # makes it through into the browser and isn't just an empty list
    def test_leaderboard_shows_seeded_top_player(self):
        self._login()
        self.driver.get(f'{BASE_URL}/play/kai')
        WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.ID, 'kaiCanvas')))
        body_text = self.driver.find_element(By.TAG_NAME, 'body').text
        self.assertIn('Top 3', body_text)
        self.assertIn('Top Player', body_text)


if __name__ == '__main__':
    unittest.main()
