import time
import unittest

from twilio import jwt

from twilio.task_router import TaskRouterCapability


class TaskRouterCapabilityTest(unittest.TestCase):

    def setUp(self):
        self.account_sid = "AC123"
        self.auth_token = "foobar"
        self.workspace_sid = "WS456"
        self.worker_sid = "WK789"
        self.cap = TaskRouterCapability(self.account_sid, self.auth_token,
                                        self.workspace_sid, self.worker_sid)

    def test_generate_token(self):
        token = self.cap.generate_token()
        decoded = jwt.decode(token, self.auth_token)

        self.assertIsNotNone(decoded)
        del decoded['exp']
        del decoded['policies']

        expected = {
            'iss': self.account_sid,
            'account_sid': self.account_sid,
            'workspace_sid': self.workspace_sid,
            'worker_sid': self.worker_sid,
            'channel': self.worker_sid,
            'version': 'v1',
            'friendly_name': self.worker_sid,
        }
        self.assertDictEqual(expected, decoded)

    def test_generate_token_default_ttl(self):
        token = self.cap.generate_token()
        decoded = jwt.decode(token, self.auth_token)

        self.assertIsNotNone(decoded)
        self.assertEqual(int(time.time()) + 3600, decoded['exp'])

    def test_generate_token_custom_ttl(self):
        token = self.cap.generate_token(10000)
        decoded = jwt.decode(token, self.auth_token)

        self.assertIsNotNone(decoded)
        self.assertEqual(int(time.time()) + 10000, decoded['exp'])

    def test_defaults(self):
        token = self.cap.generate_token()
        decoded = jwt.decode(token, self.auth_token)

        self.assertIsNotNone(decoded)
        websocket_url = (
            'https://event-bridge.twilio.com/v1/wschannels/%s/%s' %
            (self.account_sid, self.worker_sid)
        )
        expected = [
            {
                'url': websocket_url,
                'method': 'GET',
                'allow': True,
                'query_filter': {},
                'post_filter': {},
            },
            {
                'url': websocket_url,
                'method': 'POST',
                'allow': True,
                'query_filter': {},
                'post_filter': {},
            },
            {
                'url':
                'https://taskrouter.twilio.com/v1/Workspaces/WS456/Activities',
                'method': 'GET',
                'allow': True,
                'query_filter': {},
                'post_filter': {},
            },
        ]
        self.assertEqual(expected, decoded['policies'])

    def test_allow_worker_activity_updates(self):
        self.cap.allow_worker_activity_updates()
        token = self.cap.generate_token()
        decoded = jwt.decode(token, self.auth_token)

        self.assertIsNotNone(decoded)
        url = 'https://taskrouter.twilio.com/v1/Workspaces/%s/Workers/%s' % (
            self.workspace_sid,
            self.worker_sid,
        )

        expected = {
            'url': url,
            'method': 'POST',
            'allow': True,
            'query_filter': {},
            'post_filter': {'ActivitySid': {'required': True}},
        }
        self.assertEqual(expected, decoded['policies'][-1])

    def test_allow_worker_fetch_attributes(self):
        self.cap.allow_worker_fetch_attributes()
        token = self.cap.generate_token()
        decoded = jwt.decode(token, self.auth_token)

        self.assertIsNotNone(decoded)
        url = 'https://taskrouter.twilio.com/v1/Workspaces/%s/Workers/%s' % (
            self.workspace_sid,
            self.worker_sid,
        )

        expected = {
            'url': url,
            'method': 'GET',
            'allow': True,
            'query_filter': {},
            'post_filter': {},
        }

        self.assertEqual(expected, decoded['policies'][-1])

    def test_allow_task_reservation_updates(self):
        self.cap.allow_task_reservation_updates()
        token = self.cap.generate_token()
        decoded = jwt.decode(token, self.auth_token)

        self.assertIsNotNone(decoded)
        url = 'https://taskrouter.twilio.com/v1/Workspaces/%s/Tasks/**' % (
            self.workspace_sid,
        )

        expected = {
            'url': url,
            'method': 'POST',
            'allow': True,
            'query_filter': {},
            'post_filter': {'ReservationStatus': {'required': True}},
        }
        self.assertEqual(expected, decoded['policies'][-1])
