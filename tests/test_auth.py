import unittest

from app import create_app
from app.config import TestingConfig
from app.models import User, db


class AuthTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestingConfig)
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        self.client = self.app.test_client()

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
