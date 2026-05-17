"""
TicTacToe test suite — unit tests and Selenium end-to-end tests.

Unit tests use Flask's test client (no browser required).
Selenium tests spin up a live Werkzeug server on port 5001.

Requirements (Selenium only):
    pip install selenium
    ChromeDriver on PATH matching your Chrome version:
    https://googlechromelabs.github.io/chrome-for-testing/

Run all tests:
    python -m unittest tests.tictactoeTesting
"""

import os
import tempfile
import threading
import time
import unittest

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from app import create_app
from app.config import TestingConfig
from app.models import TicTacToeRun, User, db

PORT = 5001
BASE_URL = f'http://localhost:{PORT}'
TEST_USERNAME = 'selenium_user'
TEST_PASSWORD = 'seleniumpass1'


class _SeleniumConfig(TestingConfig):
    # URI is patched in setUpClass once the temp file path is known
    pass


# ======================================================================
# Unit tests  (Flask test client, no browser)
# ======================================================================

class TicTacToeUnitTests(unittest.TestCase):

    def setUp(self):
        self.app = create_app(TestingConfig)
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        self.client = self.app.test_client()

        user = User(username='tttplayer')
        user.set_password('password1')
        db.session.add(user)
        db.session.commit()
        self.user_id = user.id

        # log in so every test runs with an authenticated session
        self.client.post('/', data={'username': 'tttplayer', 'password': 'password1'})

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_page_loads_when_authenticated(self):
        res = self.client.get('/tictactoe')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'RNG Tic-Tac-Toe', res.data)

    def test_api_records_win(self):
        res = self.client.post('/api/tictactoe/runs', json={'result': 'win', 'time_ms': 5000})
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.get_json()['ok'])
        run = TicTacToeRun.query.filter_by(user_id=self.user_id).first()
        self.assertEqual(run.wins, 1)
        self.assertEqual(run.best_win_ms, 5000)

    def test_api_records_loss(self):
        self.client.post('/api/tictactoe/runs', json={'result': 'loss'})
        run = TicTacToeRun.query.filter_by(user_id=self.user_id).first()
        self.assertEqual(run.losses, 1)

    def test_api_records_draw(self):
        self.client.post('/api/tictactoe/runs', json={'result': 'draw'})
        run = TicTacToeRun.query.filter_by(user_id=self.user_id).first()
        self.assertEqual(run.draws, 1)

    def test_api_updates_best_time_when_faster(self):
        self.client.post('/api/tictactoe/runs', json={'result': 'win', 'time_ms': 10000})
        self.client.post('/api/tictactoe/runs', json={'result': 'win', 'time_ms': 3000})
        run = TicTacToeRun.query.filter_by(user_id=self.user_id).first()
        self.assertEqual(run.best_win_ms, 3000)
        self.assertEqual(run.wins, 2)

    def test_api_keeps_best_time_when_slower(self):
        self.client.post('/api/tictactoe/runs', json={'result': 'win', 'time_ms': 3000})
        self.client.post('/api/tictactoe/runs', json={'result': 'win', 'time_ms': 10000})
        run = TicTacToeRun.query.filter_by(user_id=self.user_id).first()
        self.assertEqual(run.best_win_ms, 3000)

    def test_api_win_without_time_ms_rejected(self):
        res = self.client.post('/api/tictactoe/runs', json={'result': 'win'})
        self.assertEqual(res.status_code, 400)

    def test_api_invalid_result_rejected(self):
        res = self.client.post('/api/tictactoe/runs', json={'result': 'cheat'})
        self.assertEqual(res.status_code, 400)



# ======================================================================
# Selenium tests  (live Werkzeug server on port 5001)
# ======================================================================

class TicTacToeSeleniumTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # File-based SQLite so the Flask server thread and the test thread
        # both read from the same database (in-memory would be per-connection).
        cls._db_fd, cls._db_path = tempfile.mkstemp(suffix='.db')
        _SeleniumConfig.SQLALCHEMY_DATABASE_URI = f'sqlite:///{cls._db_path}'

        cls.app = create_app(_SeleniumConfig)
        cls.app_ctx = cls.app.app_context()
        cls.app_ctx.push()
        db.create_all()

        user = User(username=TEST_USERNAME)
        user.set_password(TEST_PASSWORD)
        db.session.add(user)
        db.session.commit()
        cls.user_id = user.id

        cls._server = threading.Thread(
            target=lambda: cls.app.run(port=PORT, use_reloader=False),
            daemon=True,
        )
        cls._server.start()
        time.sleep(1)  # give Werkzeug time to bind the port

        opts = Options()
        opts.add_argument('--headless')
        opts.add_argument('--no-sandbox')
        opts.add_argument('--disable-dev-shm-usage')
        opts.add_argument('--window-size=1280,800')
        cls.driver = webdriver.Chrome(options=opts)
        cls.wait = WebDriverWait(cls.driver, 5)

        # Log in once — session cookie persists across all tests
        cls.driver.get(f'{BASE_URL}/')
        cls.driver.find_element(By.ID, 'username').send_keys(TEST_USERNAME)
        cls.driver.find_element(By.ID, 'password').send_keys(TEST_PASSWORD)
        # JS click bypasses any element-interception issues in headless Chrome
        submit = WebDriverWait(cls.driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[type=submit]'))
        )
        cls.driver.execute_script("arguments[0].click();", submit)
        WebDriverWait(cls.driver, 5).until(EC.url_contains('/stages'))

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()
        db.session.remove()
        db.drop_all()
        db.engine.dispose()  # close SQLAlchemy connections before removing the file
        cls.app_ctx.pop()
        os.close(cls._db_fd)
        try:
            os.unlink(cls._db_path)
        except PermissionError:
            pass  # daemon server thread still holds the file on Windows; OS cleans it on exit

    def setUp(self):
        """Load a fresh TicTacToe page before every test."""
        self.driver.get(f'{BASE_URL}/tictactoe')
        self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'tttCell')))

    def _cells(self):
        return self.driver.find_elements(By.CLASS_NAME, 'tttCell')

    def _setup_near_win(self):
        """Inject board state so clicking cell 2 wins (top row for X)."""
        self.driver.execute_script("""
            board[0] = 'X'; cells[0].textContent = 'X';
            board[1] = 'X'; cells[1].textContent = 'X';
            board[6] = 'O'; cells[6].textContent = 'O';
            board[7] = 'O'; cells[7].textContent = 'O';
        """)

    def test_01_page_has_nine_cells(self):
        self.assertEqual(len(self._cells()), 9)

    def test_02_timer_is_present_and_ticking(self):
        timer = self.driver.find_element(By.ID, 'tttTimer')
        first = timer.text
        time.sleep(0.15)
        self.assertNotEqual(timer.text, first)

    def test_03_end_screen_hidden_on_load(self):
        end_screen = self.driver.find_element(By.ID, 'tttEndScreen')
        self.assertIn('none', end_screen.get_attribute('style'))

    def test_04_clicking_cell_places_x(self):
        cell = self._cells()[4]
        cell.click()
        time.sleep(0.1)
        self.assertEqual(cell.text, 'X')

    def test_05_win_shows_end_screen(self):
        self._setup_near_win()
        self._cells()[2].click()
        end_screen = self.wait.until(
            EC.visibility_of_element_located((By.ID, 'tttEndScreen'))
        )
        self.assertTrue(end_screen.is_displayed())

    def test_06_win_screen_title_is_you_win(self):
        self._setup_near_win()
        self._cells()[2].click()
        self.wait.until(EC.visibility_of_element_located((By.ID, 'tttEndScreen')))
        self.assertEqual(self.driver.find_element(By.ID, 'tttEndTitle').text, 'You Win!')

    def test_07_win_screen_time_has_correct_format(self):
        self._setup_near_win()
        self._cells()[2].click()
        self.wait.until(EC.visibility_of_element_located((By.ID, 'tttEndScreen')))
        time_text = self.driver.find_element(By.ID, 'tttEndTime').text
        self.assertRegex(time_text, r'^\d+\.\d{3}s$')

    def test_08_win_screen_time_matches_top_timer(self):
        self._setup_near_win()
        self._cells()[2].click()
        self.wait.until(EC.visibility_of_element_located((By.ID, 'tttEndScreen')))
        top_timer = self.driver.find_element(By.ID, 'tttTimer').text
        win_time = self.driver.find_element(By.ID, 'tttEndTime').text
        self.assertEqual(top_timer, win_time)

    def test_09_win_is_recorded_in_db(self):
        self._setup_near_win()
        self._cells()[2].click()
        self.wait.until(EC.visibility_of_element_located((By.ID, 'tttEndScreen')))
        time.sleep(0.5)  # let the async fetch reach the server and commit
        db.session.expire_all()
        run = TicTacToeRun.query.filter_by(user_id=self.user_id).first()
        self.assertIsNotNone(run)
        self.assertGreater(run.wins, 0)
        self.assertIsNotNone(run.best_win_ms)

    def test_10_best_win_ms_matches_displayed_time(self):
        # Clear any prior run so this test's win is guaranteed to be the best
        TicTacToeRun.query.filter_by(user_id=self.user_id).delete()
        db.session.commit()
        self._setup_near_win()
        self._cells()[2].click()
        self.wait.until(EC.visibility_of_element_located((By.ID, 'tttEndScreen')))
        displayed_s = self.driver.find_element(By.ID, 'tttEndTime').text
        displayed_ms = round(float(displayed_s.rstrip('s')) * 1000)
        time.sleep(0.5)
        db.session.expire_all()
        run = TicTacToeRun.query.filter_by(user_id=self.user_id).first()
        self.assertAlmostEqual(run.best_win_ms, displayed_ms, delta=1)


if __name__ == '__main__':
    unittest.main()
