import json
import unittest

from app import create_app
from app.config import TestingConfig
from app.models import User, WheresWilsonRun, db


class Game1TestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestingConfig)
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        self.client = self.app.test_client()

        self.user = User(username='wilsonTest')
        self.user.set_password('password1')
        db.session.add(self.user)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def login(self):
        return self.client.post(
            '/',
            data={'username': 'wilsonTest', 'password': 'password1'},
            follow_redirects=True,
        )

    def post_run(self, payload):
        return self.client.post(
            '/api/game1/runs',
            data=json.dumps(payload),
            content_type='application/json',
        )

    def test_game1_requires_login(self):
        response = self.client.get('/game1', follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/?next=', response.headers['Location'])

    def test_game1_renders_when_logged_in(self):
        self.login()
        response = self.client.get('/game1')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Where's Wilson", response.data)
        self.assertIn(b'start-button', response.data)

    def test_api_save_valid_run(self):
        self.login()
        response = self.post_run({'time_ms': 2500})

        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertTrue(body.get('ok'))
        self.assertTrue(body.get('is_new_best'))

        row = WheresWilsonRun.query.filter_by(user_id=self.user.id).one()
        self.assertEqual(row.time_ms, 2500)
    
    def test_api_slower_run_keeps_existing_best(self):
        self.login()

        self.post_run({'time_ms': 2000})
        response = self.post_run({'time_ms': 3000})

        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertTrue(body.get('ok'))
        self.assertFalse(body.get('is_new_best'))

        row = WheresWilsonRun.query.filter_by(user_id=self.user.id).one()
        self.assertEqual(row.time_ms, 2000)


if __name__ == '__main__':
    unittest.main()