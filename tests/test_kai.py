import json
import unittest

from app import create_app
from app.config import TestingConfig
from app.models import KaiRun, User, db


class KaiTestCase(unittest.TestCase):
    def setUp(self):
        # spin up a fresh in-memory app for every test so rows don't bleed across
        self.app = create_app(TestingConfig)
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        self.client = self.app.test_client()

        # one user for the login-required routes, password hashed via the model helper
        self.user = User(username='kaiTest')
        self.user.set_password('password1')
        db.session.add(self.user)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def login(self):
        # hits the real login form so flask-login actually sets the session cookie
        return self.client.post(
            '/',
            data={'username': 'kaiTest', 'password': 'password1'},
            follow_redirects=True,
        )

    def post_run(self, payload):
        # WTF_CSRF_ENABLED is off in TestingConfig so we skip the X-CSRFToken header here
        return self.client.post(
            '/api/kai/runs',
            data=json.dumps(payload),
            content_type='application/json',
        )

    # 1) anon users get bounced to login when they hit the game page
    def test_play_kai_requires_login(self):
        response = self.client.get('/play/kai', follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/?next=', response.headers['Location'])

    # 2) logged in users get the Snack-Time canvas page
    def test_play_kai_renders_canvas_when_logged_in(self):
        self.login()
        response = self.client.get('/play/kai')
        self.assertEqual(response.status_code, 200)
        # canvas tag id is the easiest thing to grep for in the rendered html
        self.assertIn(b'kaiCanvas', response.data)
        self.assertIn(b'Snack-Time', response.data)

    # 3) a valid run payload saves a row tied to the logged in user
    def test_api_save_valid_run(self):
        self.login()
        response = self.post_run({'time_ms': 5000, 'avg_eat_ms': 800, 'eat_count': 6})
        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertTrue(body.get('ok'))
        # row should exist with the values we posted
        row = KaiRun.query.filter_by(user_id=self.user.id).one()
        self.assertEqual(row.time_ms, 5000)
        self.assertEqual(row.avg_eat_ms, 800)
        self.assertEqual(row.eat_count, 6)

    # 4) negative time_ms is garbage so the server rejects it with 400 and stores nothing
    def test_api_rejects_negative_time(self):
        self.login()
        response = self.post_run({'time_ms': -1, 'avg_eat_ms': 0, 'eat_count': 0})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(KaiRun.query.count(), 0)

    # 5) a better run (longer survival time) replaces the older row
    def test_api_higher_time_overwrites_existing(self):
        self.login()
        self.post_run({'time_ms': 1000, 'avg_eat_ms': 500, 'eat_count': 3})
        self.post_run({'time_ms': 2000, 'avg_eat_ms': 800, 'eat_count': 5})
        # still one row per user, the bigger time wins
        rows = KaiRun.query.filter_by(user_id=self.user.id).all()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].time_ms, 2000)
        self.assertEqual(rows[0].eat_count, 5)

    # 6) a worse run (shorter time) gets thrown out, old best stays put
    def test_api_lower_time_keeps_existing(self):
        self.login()
        self.post_run({'time_ms': 2000, 'avg_eat_ms': 800, 'eat_count': 5})
        body = self.post_run({'time_ms': 500, 'avg_eat_ms': 200, 'eat_count': 1}).get_json()
        # is_new_best should be false so the client knows not to reload
        self.assertFalse(body.get('is_new_best'))
        row = KaiRun.query.filter_by(user_id=self.user.id).one()
        self.assertEqual(row.time_ms, 2000)


if __name__ == '__main__':
    unittest.main()
