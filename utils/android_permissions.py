from kivy.utils import platform
from plyer.utils import platform as plyer_platform
from functools import partial

# Android permission constants
class AndroidPermissionConstants:
    WRITE_EXTERNAL_STORAGE = "android.permission.WRITE_EXTERNAL_STORAGE"
    READ_EXTERNAL_STORAGE = "android.permission.READ_EXTERNAL_STORAGE"
    ACCESS_COARSE_LOCATION = "android.permission.ACCESS_COARSE_LOCATION"
    ACCESS_FINE_LOCATION = "android.permission.ACCESS_FINE_LOCATION"

class AndroidPermissions:
    """Handle Android permissions using plyer"""
    
    def __init__(self):
        self.permission_states = {}
        self._permission_map = {
            'storage': [
                AndroidPermissionConstants.WRITE_EXTERNAL_STORAGE,
                AndroidPermissionConstants.READ_EXTERNAL_STORAGE
            ],
            'location': [
                AndroidPermissionConstants.ACCESS_COARSE_LOCATION,
                AndroidPermissionConstants.ACCESS_FINE_LOCATION
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
            
        for perm in permissions:
            if platform == 'android':
                from android.permissions import check_permission
                if not check_permission(perm):
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
            
        if platform == 'android':
            from android.permissions import request_permissions
            request_permissions(
                permissions,
                partial(on_permissions_callback, permissions)
            )
        
    def ensure_permissions(self, required_permissions, success_callback, failure_callback=None):
        """
        Ensure all required permissions are granted
        
        Args:
            required_permissions (list): List of permission types to check
            success_callback (callable): Called when all permissions granted
            failure_callback (callable, optional): Called if permissions denied
        """
        def check_next_permission(permissions, index=0):
            if index >= len(permissions):
                success_callback()
                return
                
            current_permission = permissions[index]
            
            def on_permission_result(granted):
                if granted:
                    check_next_permission(permissions, index + 1)
                elif failure_callback:
                    failure_callback()
                    
            if self.check_permission(current_permission):
                check_next_permission(permissions, index + 1)
            else:
                self.request_permission(current_permission, on_permission_result)
                
        check_next_permission(required_permissions)