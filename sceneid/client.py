import urllib.parse

import requests


class SceneIDError(Exception):
    """SceneID could not be reached, or gave an answer we can't use."""


class SceneIDClient:
    def __init__(self, client_id, client_secret, hostname='id.scene.org', timeout=5):
        self.client_id = client_id
        self.client_secret = client_secret
        self.hostname = hostname
        # seconds to wait for id.scene.org, so a slow SceneID doesn't tie up a web worker
        self.timeout = timeout

    def get_authorization_uri(self, state, redirect_uri, scopes=None):
        params = {
            'client_id': self.client_id,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'state': state,
        }
        if scopes:
            params['scope'] = ' '.join(scopes)

        return "https://%s/oauth/authorize/?%s" % (
            self.hostname,
            urllib.parse.urlencode(params)
        )

    def _request(self, method, url, **kwargs):
        try:
            response = requests.request(method, url, timeout=self.timeout, **kwargs)
        except requests.RequestException as e:
            raise SceneIDError("Could not reach SceneID: %s" % e) from e
        try:
            return response.json()
        except ValueError as e:
            raise SceneIDError("Invalid response from SceneID (HTTP %s)" % response.status_code) from e

    def get_access_token(self, code, redirect_uri):
        url = "https://%s/oauth/token/" % self.hostname
        return self._request(
            'POST',
            url,
            data={
                'grant_type': 'authorization_code',
                'code': code,
                'redirect_uri': redirect_uri,
            },
            auth=(self.client_id, self.client_secret),
        )

    def get_user_data(self, access_token):
        url = "https://%s/api/3.0/me/" % self.hostname
        return self._request(
            'GET',
            url,
            headers={'Authorization': "Bearer %s" % access_token}
        )
