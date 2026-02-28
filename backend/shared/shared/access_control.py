from shared.data_store import DataStore

PERMISSION_MATRIX = {
    'admin':    {'view': True, 'upload': True, 'download': True},
    'uploader': {'view': True, 'upload': True, 'download': True},
    'reader':   {'view': True, 'upload': False, 'download': True},
    'viewer':   {'view': True, 'upload': False, 'download': False},
}


class AccessControl:
    def __init__(self, data_store=None):
        self.ds = data_store or DataStore()

    def check_admin(self, role):
        return role == 'admin'

    def check_folder_access(self, username, role, folder_name):
        if role == 'admin':
            return True
        assignment = self.ds.get_item(f'USER#{username}', f'FOLDER#{folder_name}')
        return assignment is not None

    def check_file_action(self, role, action):
        perms = PERMISSION_MATRIX.get(role, {})
        return perms.get(action, False)

    def authorize(self, username, role, folder_name, action):
        if not self.check_folder_access(username, role, folder_name):
            return False
        return self.check_file_action(role, action)
