import time
from shared.data_store import DataStore


class SessionValidator:
    def __init__(self, data_store=None):
        self.ds = data_store or DataStore()

    def validate(self, event):
        """Extract and validate session token from Authorization header.
        Returns dict with username and role, or raises an error dict."""
        headers = event.get('headers') or {}
        # API Gateway lowercases header names
        token = headers.get('Authorization') or headers.get('authorization') or ''
        token = token.replace('Bearer ', '')
        if not token:
            return None

        session = self.ds.get_item(f'SESSION#{token}', f'SESSION#{token}')
        if not session:
            return None

        # Check TTL
        ttl = session.get('ttl', 0)
        if int(ttl) < int(time.time()):
            self.ds.delete_item(f'SESSION#{token}', f'SESSION#{token}')
            return None

        return {
            'username': session['username'],
            'role': session['role'],
            'token': token,
        }
