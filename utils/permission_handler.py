from kivy.utils import platform
from functools import partial
from jnius import autoclass
from jnius import autoclass
from android.permissions import request_permissions, Permission

class PermissionHandler:
    """Handle Android permissions using android.permissions"""
    
    def __init__(self):
        self.permission_states = {}
        self._permission_map = {
            'storage': [
                'android.permission.WRITE_EXTERNAL_STORAGE',
                'android.permission.READ_EXTERNAL_STORAGE'
            ],
            'location': [
                'android.permission.ACCESS_COARSE_LOCATION',
                'android.permission.ACCESS_FINE_LOCATION'
            ],
            'contacts': [
                'android.permission.READ_CONTACTS',
                'android.permission.WRITE_CONTACTS'
            ],
            'bluetooth': [
                'android.permission.BLUETOOTH',
                'android.permission.BLUETOOTH_ADMIN',
                'android.permission.BLUETOOTH_SCAN',
                'android.permission.BLUETOOTH_CONNECT',
                'android.permission.BLUETOOTH_ADVERTISE'
            ]
        }
    
    def _get_permissions_for_type(self, permission_type):
        """Get the list of permissions for a given type"""
        return self._permission_map.get(permission_type, [])
    
    def check_permission(self, permission_type):
        """Check if a permission is granted"""
        if platform != 'android':
            return True
            
        permissions = self._get_permissions_for_type(permission_type)
        if not permissions:
            print(f"Warning: Unknown permission type {permission_type}")
            return False
            
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        activity = PythonActivity.mActivity
        context = activity.getApplicationContext()
        PackageManager = autoclass('android.content.pm.PackageManager')
            
        for perm in permissions:
            if context.checkSelfPermission(perm) != PackageManager.PERMISSION_GRANTED:
                return False
        return True
    
    def request_permission(self, permission_type, callback=None):
        """Request a permission"""
        if platform != 'android':
            if callback:
                callback(True)
            return True
            
        permissions = self._get_permissions_for_type(permission_type)
        if not permissions:
            print(f"Warning: Unknown permission type {permission_type}")
            if callback:
                callback(False)
            return False
        
        def on_permissions_callback(permissions, grants):
            granted = all(grants)
            if callback:
                callback(granted)
            return granted
        
        # Use android.permissions module to request permissions
        request_permissions(
            permissions,
            partial(on_permissions_callback, permissions)
        )
        return True
    
    def check_storage_permission(self):
        """Check storage permission"""
        return self.check_permission('storage')
    
    def check_location_permission(self):
        """Check location permission"""
        return self.check_permission('location')
    
    def check_contacts_permission(self):
        """Check contacts permission"""
        return self.check_permission('contacts')
    
    def check_bluetooth_permission(self):
        """Check bluetooth permission"""
        return self.check_permission('bluetooth')
    
    def request_storage_permission(self):
        """Request storage permission"""
        return self.request_permission('storage')
    
    def request_location_permission(self):
        """Request location permission"""
        return self.request_permission('location')
    
    def request_contacts_permission(self):
        """Request contacts permission"""
        return self.request_permission('contacts')
    
    def request_bluetooth_permission(self):
        """Request bluetooth permission"""
        return self.request_permission('bluetooth')