from unittest.mock import patch

from django.contrib.auth import get_user
from django.contrib.messages import get_messages
from django.test import TestCase
import requests
import responses

from sceneid.client import SceneIDClient, SceneIDError

TOKEN_URL = 'https://id.scene.org/oauth/token/'
ME_URL = 'https://id.scene.org/api/3.0/me/'
LOGIN = '/account/sceneid/login/?state=66666666&code=4321432143214321'


class TestLoginErrors(TestCase):
    """Every way the SceneID round trip can fail ends on the login page with a message."""

    def start_login(self):
        with patch('sceneid.views.get_random_string', return_value='66666666'):
            self.client.get('/account/sceneid/auth/')

    def assertFailed(self, response, message):
        self.assertRedirects(response, '/accounts/login/', fetch_redirect_response=False)
        # the newest message (an earlier step's may still be queued: redirects aren't followed)
        self.assertEqual(str(list(get_messages(response.wsgi_request))[-1]), message)
        self.assertFalse(get_user(self.client).is_authenticated)

    def test_denied(self):
        self.start_login()
        response = self.client.get('/account/sceneid/login/?error=access_denied&state=66666666')
        self.assertFailed(response, "SceneID login was cancelled.")

    def test_no_session(self):
        # e.g. the session expired while the user was on SceneID
        response = self.client.get(LOGIN)
        self.assertFailed(response, "Your SceneID login expired. Please try again.")

    def test_missing_code(self):
        self.start_login()
        response = self.client.get('/account/sceneid/login/?state=66666666')
        self.assertFailed(response, "Your SceneID login expired. Please try again.")

    @responses.activate
    def test_state_used_once(self):
        responses.add(responses.POST, TOKEN_URL, json={'error': 'invalid_grant'})
        self.start_login()
        self.client.get(LOGIN)
        response = self.client.get(LOGIN)
        self.assertFailed(response, "Your SceneID login expired. Please try again.")

    @responses.activate
    def test_token_error(self):
        responses.add(responses.POST, TOKEN_URL, status=400, json={'error': 'invalid_grant'})
        self.start_login()
        response = self.client.get(LOGIN)
        self.assertFailed(response, "SceneID couldn't log you in just now. Please try again later.")

    @responses.activate
    def test_timeout(self):
        responses.add(responses.POST, TOKEN_URL, body=requests.exceptions.ConnectTimeout())
        self.start_login()
        response = self.client.get(LOGIN)
        self.assertFailed(response, "SceneID couldn't log you in just now. Please try again later.")

    @responses.activate
    def test_not_json(self):
        responses.add(responses.POST, TOKEN_URL, status=502, body='<html>Bad gateway</html>')
        self.start_login()
        response = self.client.get(LOGIN)
        self.assertFailed(response, "SceneID couldn't log you in just now. Please try again later.")

    @responses.activate
    def test_bad_user_data(self):
        responses.add(responses.POST, TOKEN_URL, json={'access_token': '5678'})
        responses.add(responses.GET, ME_URL, json={'success': False})
        self.start_login()
        response = self.client.get(LOGIN)
        self.assertFailed(response, "SceneID couldn't log you in just now. Please try again later.")


class TestClientErrors(TestCase):
    def setUp(self):
        self.sceneid_client = SceneIDClient('testsite', 'secret', timeout=3)

    @responses.activate
    def test_timeout_is_passed(self):
        seen = {}

        def callback(request):
            seen['timeout'] = request.req_kwargs.get('timeout')
            return (200, {}, '{"access_token": "x"}')

        responses.add_callback(responses.POST, TOKEN_URL, callback=callback)
        self.sceneid_client.get_access_token('code', 'https://testsite/')
        self.assertEqual(seen['timeout'], 3)

    @responses.activate
    def test_connection_error(self):
        responses.add(responses.GET, ME_URL, body=requests.exceptions.ConnectionError('down'))
        with self.assertRaises(SceneIDError):
            self.sceneid_client.get_user_data('token')
