from kivy.utils import platform

# Import platform-specific modules conditionally
if platform == 'android':
    try:
        from kvdroid.tools.contact import get_contact_details
        from android.permissions import request_permissions, Permission
    except ImportError as e:
        print(f"Error importing Android-specific modules: {e}")

class ContactService:
    """Service for handling contact-related operations"""
    
    @staticmethod
    def request_contact_permissions(callback=None):
        """Request Android contact permissions"""
        if platform != 'android':
            if callback:
                callback([], [True, True])
            return
            
        def default_callback(permissions, results):
            if all([res for res in results]):
                print("Contact permissions granted.")
            else:
                print("Some contact permissions were refused.")
        
        try:
            request_permissions(
                [Permission.READ_CONTACTS, Permission.WRITE_CONTACTS],
                callback or default_callback
            )
        except Exception as e:
            print(f"Error requesting contact permissions: {e}")
            if callback:
                callback([], [False, False])
    
    @staticmethod
    def get_all_contacts():
        """Get all contacts with their names and phone numbers"""
        return get_contact_details("phone_book")
    
    @staticmethod
    def get_contact_names():
        """Get list of all contact names"""
        return get_contact_details("names")
    
    @staticmethod
    def get_contact_numbers():
        """Get list of all contact phone numbers"""
        return get_contact_details("mobile_no")