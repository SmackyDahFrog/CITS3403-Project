import unittest

from app import create_app
from app.config import TestingConfig
from app.models import User, db
from app.routes import _username_check_hits


class AuthTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestingConfig)
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        self.client = self.app.test_client()
        # rate limit dict is module-level, wipe so tests don't bleed into each other
        _username_check_hits.clear()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_signup_creates_user(self):
        response = self.client.post(
            '/signup',
            data={
                'username': 'kaiTest',
                'password': 'password1',
                'confirm_password': 'password1',
            },
            follow_redirects=False,
        )
        #  successful signup redirects to customisation
        self.assertEqual(response.status_code, 302)
        self.assertIn('/customisation', response.headers['Location'])
        self.assertIsNotNone(User.query.filter_by(username='kaiTest').first())

    def test_check_username_available(self):
        # nothing in the table yet, the name should come back as available
        response = self.client.get('/check-username?username=freshName')
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertTrue(payload['available'])

    def test_check_username_taken(self):
        # existing user blocks the same name from being marked available
        user = User(username='kaiTest')
        user.set_password('password1')
        db.session.add(user)
        db.session.commit()

        response = self.client.get('/check-username?username=kaiTest')
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertFalse(payload['available'])
        self.assertEqual(payload['reason'], 'taken')

    def test_check_username_too_short(self):
        # short names are flagged before we even hit the database
        response = self.client.get('/check-username?username=ab')
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertFalse(payload['available'])
        self.assertEqual(payload['reason'], 'short')

    def test_check_username_rejects_special_chars(self):
        # spaces and punctuation should not be accepted as usernames
        response = self.client.get('/check-username?username=bad name')
        payload = response.get_json()
        self.assertFalse(payload['available'])
        self.assertEqual(payload['reason'], 'invalid')

    def test_check_username_rate_limited(self):
        # past the per-window limit the endpoint should refuse with 429
        for _ in range(20):
            self.client.get('/check-username?username=spammer')
        response = self.client.get('/check-username?username=spammer')
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.get_json()['reason'], 'rate_limited')

    def test_signup_failed_preserves_username(self):
        # too-short password fails validation, the username should still be in the form
        response = self.client.post(
            '/signup',
            data={'username': 'kaiTest', 'password': 'pw', 'confirm_password': 'pw'},
            follow_redirects=False,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'value="kaiTest"', response.data)

    def test_signup_failed_does_not_echo_password(self):
        # passwords must never round-trip back to the rendered HTML
        response = self.client.post(
            '/signup',
            data={'username': 'ab', 'password': 'TopSecret9!', 'confirm_password': 'TopSecret9!'},
            follow_redirects=False,
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b'TopSecret9!', response.data)

    @unittest.expectedFailure
    def test_login_with_wrong_password_fails(self):
        """Expected to fail until MainPage.html renders flashed messages."""
        user = User(username='kaiTest')
        user.set_password('password1')
        db.session.add(user)
        db.session.commit()

        response = self.client.post(
            '/',
            data={'username': 'kaiTest', 'password': 'wrongpass'},
            follow_redirects=True,
        )
        #stays on the login page when credentials are bad
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Invalid username or password', response.data)


if __name__ == '__main__':
    unittest.main()
