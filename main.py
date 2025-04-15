import os
import sys
from dotenv import load_dotenv
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition
from kivy.core.window import Window
from kivy.properties import ObjectProperty, StringProperty, BooleanProperty
from kivy.lang import Builder
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.resources import resource_add_path
from kivy.cache import Cache
import random
import string
import json
import traceback
from utils.android_permissions import AndroidPermissions

# Add the project root directory to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
resource_add_path(project_root)

# Import screens
from screens.homepage.home_screen import HomeScreen
from screens.login.login_screen import LoginScreen
from screens.signup.email_signup_screen import EmailSignupScreen
from screens.profile.profile_setup_screen import ProfileSetupScreen
from screens.profile.profile_view_screen import ProfileViewScreen
#from screens.welcome.welcome_screen import WelcomeScreen
from screens.flags.flags_screen import FlagsScreen
from screens.phone.phone_number_screen import PhoneNumberScreen
from screens.verify.verify_screen import VerifyScreen
from screens.permissions.permissions_screen import PermissionsScreen
from screens.profile_update.profile_update_screen import ProfileUpdateScreen
from screens.info.info_screen import InfoMainScreen
from screens.terminate_account.terminate_account_screen import TerminateAccountScreen
from screens.bluetooth.bluetooth_screen import BluetoothScreen
from screens.accidental_press.accidental_press_screen import AccidentalPressScreen

class DatabaseError(Exception):
    """Custom exception for database operations"""
    pass

class SafinityApp(App):
    # Screen manager
    sm = ObjectProperty(None)
    
    # User data properties
    user_id = StringProperty('')
    email = StringProperty('')
    password = StringProperty('')
    phone_number = StringProperty('')
    verification_code = StringProperty('')
    country_code = StringProperty('')
    selected_country = ObjectProperty(None, allownone=True)
    
    # State properties
    is_verified = BooleanProperty(False)
    
    def __init__(self, **kwargs):
        try:
            super(SafinityApp, self).__init__(**kwargs)
            self._popup = None
            self.user_data = {}
            Window.size = (400, 600)
            self.title = 'Safinity'
            # Initialize Android permissions handler
            self.android_permissions = AndroidPermissions()
            # Clear caches on startup to prevent stale image data
            self.clear_caches()
            self.load_user_data()
        except Exception as e:
            print(f"Error initializing SafinityApp: {str(e)}")
            print(traceback.format_exc())

    def build(self):
        """Initialize app and load screens"""
        # Set default user as empty string (not None)
        self.user_id = ""  # Using empty string instead of None
        self.user_data = None
        self.tutorial_viewed = False
        
        # Initialize database and ensure tables are created
        from utils.database_service import DatabaseService
        db = DatabaseService()
        db.create_tables()  # Ensure all tables and columns exist
        
        # Create screen manager
        self.sm = ScreenManager(transition=NoTransition())
        
        # Load KV files first
        try:
            print("Loading KV files...")
            kv_files = [
                ('homepage', 'home_screen.kv'),  # Moved home screen KV first
                ('login', 'login_screen.kv'),
                ('signup', 'email_signup_screen.kv'),
                ('profile', 'profile_setup_screen.kv'),
                ('profile', 'profile_view_screen.kv'),
                ('flags', 'flags_screen.kv'),
                ('phone', 'phone_number_screen.kv'),
                ('verify', 'verify_screen.kv'),
                ('permissions', 'permissions_screen.kv'),
                ('profile_update', 'profile_update_screen.kv'),
                ('info', 'info_screen.kv'),  # Add info screen KV file
                ('terminate_account', 'terminate_account_screen.kv'),  # Add terminate account KV file
                ('bluetooth', 'bluetooth_screen.kv'),  # Add bluetooth screen KV file
            ('accidental_press', 'accidental_press_screen.kv'),  # Add accidental press screen KV file
            ]
            
            for folder, filename in kv_files:
                filepath = os.path.join(project_root, 'screens', folder, filename)
                if os.path.exists(filepath):
                    print(f"Loading KV file: {filepath}")
                    try:
                        Builder.load_file(filepath)
                        print(f"Successfully loaded KV file: {filepath}")
                    except Exception as e:
                        print(f"Error loading KV file {filepath}: {str(e)}")
                else:
                    print(f"Warning: KV file not found: {filepath}")
            
        except Exception as e:
            print(f"Error loading KV files: {str(e)}")
            print(traceback.format_exc())
            raise
        
        # Import and create screens
        try:
            print("Creating screen instances...")
            # Add screens with error handling
            screens = [
                ('home', HomeScreen),  # Moved home screen first
                ('login', LoginScreen),
                ('email_signup', EmailSignupScreen),
                ('flags_screen', FlagsScreen),
                ('phone', PhoneNumberScreen),
                ('verify', VerifyScreen),
                ('profile_setup', ProfileSetupScreen),
                ('profile_view', ProfileViewScreen),
                ('permissions_screen', PermissionsScreen),
                ('profile_update', ProfileUpdateScreen),
                ('info', InfoMainScreen),  # Add info screen
                ('terminate_account', TerminateAccountScreen),  # Add terminate account screen
                ('bluetooth', BluetoothScreen),  # Add bluetooth screen
            ('accidental_press', AccidentalPressScreen),  # Add accidental press screen
            ]
            
            # Print available screens before adding new ones
            print("Current screens:", self.sm.screen_names)
            
            for screen_name, screen_class in screens:
                try:
                    print(f"Creating screen: {screen_name}")
                    screen = screen_class(name=screen_name)
                    self.sm.add_widget(screen)
                    print(f"Added screen: {screen_name}")
                    # Verify screen was added
                    if screen_name in self.sm.screen_names:
                        print(f"Verified screen {screen_name} is in screen manager")
                    else:
                        print(f"WARNING: Screen {screen_name} was not added to screen manager!")
                except Exception as e:
                    print(f"Error adding screen {screen_name}: {str(e)}")
                    print(traceback.format_exc())
            
            # Print final list of available screens
            print("Final screens:", self.sm.screen_names)
            
        except Exception as e:
            print(f"Error creating screens: {str(e)}")
            print(traceback.format_exc())
            raise
        
        # Set initial screen
        print("Setting initial screen...")
        self.sm.current = 'login'
        return self.sm
        
    # CRUD Operations for User Data
    def create_user(self, user_data):
        """Create a new user entry"""
        try:
            if not isinstance(user_data, dict):
                raise ValueError("User data must be a dictionary")
            
            # Generate unique user ID if not provided
            if 'user_id' not in user_data:
                user_data['user_id'] = self.generate_user_id()
            
            # Validate required fields
            required_fields = ['email', 'password']
            for field in required_fields:
                if field not in user_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Store user data
            self.user_data = user_data
            self.save_user_data()
            return user_data['user_id']
            
        except Exception as e:
            print(f"Error creating user: {str(e)}")
            print(traceback.format_exc())
            raise DatabaseError(f"Failed to create user: {str(e)}")

    def read_user_data(self, key=None):
        """Read user data, optionally by specific key"""
        try:
            if key is None:
                return self.user_data
            return self.user_data.get(key)
        except Exception as e:
            print(f"Error reading user data: {str(e)}")
            print(traceback.format_exc())
            raise DatabaseError(f"Failed to read user data: {str(e)}")

    def update_user_data(self, key, value):
        """Update specific user data field"""
        try:
            if not key:
                raise ValueError("Key cannot be empty")
            
            self.user_data[key] = value
            self.save_user_data()
            return True
        except Exception as e:
            print(f"Error updating user data: {str(e)}")
            print(traceback.format_exc())
            raise DatabaseError(f"Failed to update user data: {str(e)}")

    def delete_user_data(self, key=None):
        """Delete user data, optionally by specific key"""
        try:
            if key is None:
                self.user_data = {}
            elif key in self.user_data:
                del self.user_data[key]
            self.save_user_data()
            return True
        except Exception as e:
            print(f"Error deleting user data: {str(e)}")
            print(traceback.format_exc())
            raise DatabaseError(f"Failed to delete user data: {str(e)}")

    def save_user_data(self):
        """Save user data to file"""
        try:
            user_dir = os.path.join(os.path.expanduser('~'), '.safinity')
            os.makedirs(user_dir, exist_ok=True)
            
            user_file = os.path.join(user_dir, 'user_data.json')
            with open(user_file, 'w') as f:
                json.dump(self.user_data, f)
                
            return True
        except Exception as e:
            print(f"Error saving user data: {str(e)}")
            print(traceback.format_exc())
            return False

    def load_user_data(self):
        """Load user data from file"""
        try:
            user_file = os.path.join(os.path.expanduser('~'), '.safinity', 'user_data.json')
            if os.path.exists(user_file):
                with open(user_file, 'r') as f:
                    self.user_data = json.load(f)
                    
                # Set user ID property if found in loaded data
                if 'user_id' in self.user_data:
                    self.user_id = self.user_data['user_id']
            return True
        except Exception as e:
            print(f"Error loading user data: {str(e)}")
            print(traceback.format_exc())
            self.user_data = {}
            return False

    def generate_user_id(self):
        """Generate a unique user ID"""
        try:
            # Generate a random string of 6 letters and digits
            letters_and_digits = string.ascii_letters + string.digits
            return ''.join(random.choice(letters_and_digits) for i in range(6))
        except Exception as e:
            print(f"Error generating user ID: {str(e)}")
            print(traceback.format_exc())
            return None

    def show_message(self, message):
        """Show popup message"""
        popup = Popup(
            title='Safinity',
            content=Label(text=message),
            size_hint=(None, None),
            size=(300, 200)
        )
        popup.open()
        
    def check_permissions(self, permission_type):
        """Check if a specific permission has been granted""" 
        try:
            # In a real app, this would check actual device permissions
            # For now, we just check our stored permissions in user data
            permissions = self.read_user_data('permissions') or {}
            return permissions.get(permission_type, False)
        except Exception as e:
            print(f"Error checking permissions: {str(e)}")
            return False
            
    def set_permission(self, permission_type, granted=True):
        """Set a specific permission status"""
        try:
            permissions = self.read_user_data('permissions') or {}
            permissions[permission_type] = granted
            self.update_user_data('permissions', permissions)
            return True
        except Exception as e:
            print(f"Error setting permission: {str(e)}")
            return False

    def generate_verification_code(self):
        """Generate a 6-digit verification code"""
        try:
            return ''.join(random.choices(string.digits, k=6))
        except Exception as e:
            print(f"Error generating verification code: {str(e)}")
            print(traceback.format_exc())
            return None

    # Permissions handling
    def check_permission(self, permission_type):
        """Check if app has a specific permission"""
        print(f"Checking permission for: {permission_type}")
        return self.android_permissions.check_permission(permission_type)
    
    def request_permission(self, permission_type, callback=None):
        """Request a specific permission"""
        print(f"Requesting permission for: {permission_type}")
        return self.android_permissions.request_permission(permission_type, callback or self._default_permission_callback)
    
    def _default_permission_callback(self, permission_type, granted):
        """Default callback for permission requests"""
        print(f"Permission {permission_type} {'granted' if granted else 'denied'}")
        self.set_permission(permission_type, granted)

    def clear_caches(self):
        """Clear all application caches to prevent stale image data"""
        try:
            print("Clearing application caches...")
            # Import cache manager
            from utils.cache_manager import cache_manager
            
            # Clear all caches including profile pictures
            cache_manager.clear_all_caches()
            
            # Clear Kivy image and texture cache
            Cache.remove('kv.image')
            Cache.remove('kv.texture')
            
            print("Application caches cleared successfully")
            return True
        except Exception as e:
            print(f"Error clearing caches: {str(e)}")
            print(traceback.format_exc())
            return False
    
    def clear_user_data(self):
        """Clear all user data from app and device storage"""
        try:
            # Clear app properties
            self.user_id = None
            self.user_name = ""
            self.user_email = ""
            self.user_phone = ""
            
            # Clear stored data
            user_dir = os.path.join(os.path.expanduser('~'), '.safinity')
            os.makedirs(user_dir, exist_ok=True)
            
            user_file = os.path.join(user_dir, 'user_data.json')
            self.user_data_file = user_file
            
            if os.path.exists(self.user_data_file):
                os.remove(self.user_data_file)
                print("User data file removed")
            
            # Also clear caches when clearing user data
            self.clear_caches()
            
            return True
        except Exception as e:
            print(f"Error clearing user data: {str(e)}")
            return False

if __name__ == '__main__':
    try:
        print("Starting Safinity application...")
        load_dotenv()
        app = SafinityApp()
        print("Running application...")
        app.run()
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        print(traceback.format_exc())
