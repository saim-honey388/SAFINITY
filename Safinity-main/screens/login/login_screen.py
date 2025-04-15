from kivy.uix.screenmanager import Screen
from kivy.app import App
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from utils.database_service import DatabaseService
from utils.phone_util import normalize_phone_number, find_phone_number_variants
import traceback
import hashlib

class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db = DatabaseService()

    def validate_and_proceed(self):
        """Validate user credentials and proceed to home screen if valid"""
        identifier = self.ids.email_phone_input.text
        password = self.ids.password_input.text
        
        print("Starting validation...")
        print(f"Available screens before navigation: {App.get_running_app().root.screen_names}")
        
        # Debug output for login attempt
        print("\n=== Login Attempt Debug ===")
        print(f"Attempting to find user with email/phone: {identifier}")
        
        # Check if identifier looks like a phone number (no @ symbol)
        if '@' not in identifier:
            # Try to normalize as a phone number
            try:
                normalized_phone = normalize_phone_number(identifier)
                print(f"Normalized phone: {normalized_phone}")
                
                # If different from original, use both for lookup
                if normalized_phone != identifier:
                    print(f"Using normalized phone number for lookup: {normalized_phone}")
                    # The database_service's get_user_by_credentials will now handle phone variants
            except Exception as e:
                print(f"Failed to normalize phone number: {str(e)}")
                # Continue with original identifier
        
        app = App.get_running_app()
        
        # Initialize user_data if it doesn't exist
        if not hasattr(app, 'user_data') or app.user_data is None:
            app.user_data = {}
        
        # Get database service
        db = DatabaseService()
        
        # Attempt to find user by email or phone
        user_data = db.get_user_by_credentials(identifier, password)
        
        if not user_data:
            print(f"ERROR: No user found with email/phone: {identifier}")
            self.show_message("Error", "Invalid email/phone or password")
            return
            
        # The database service already verified the password - no need to check again
        # Just proceed with login
        app.user_data = user_data
        app.user_id = str(user_data.get('id'))  # Convert to string to match StringProperty type
        print(f"Login successful for user: {user_data.get('email')} (ID: {app.user_id})")
        
        # Navigate to home screen
        if 'home' in self.manager.screen_names:
            self.manager.current = 'home'
        else:
            print("Home screen not found, creating it...")
            from screens.homepage.home_screen import HomeScreen
            home_screen = HomeScreen(name='home')
            self.manager.add_widget(home_screen)
            self.manager.current = 'home'

    def show_error(self, message):
        """Show error message popup"""
        popup = Popup(
            title='Error',
            content=Label(
                text=message,
                color=(1, 1, 1, 1)
            ),
            size_hint=(None, None),
            size=(300, 150),
            background_color=(0.8, 0.2, 0.2, 1)
        )
        popup.open()

    def on_enter(self):
        print("Login screen entered")  # Debug print
    
    def show_message(self, title, message):
        """Show a popup message with title and message"""
        popup = Popup(
            title=title,
            content=Label(text=message, text_size=(280, None), halign='center'),
            size_hint=(None, None),
            size=(300, 200)
        )
        popup.open()
    
    def validate_input(self):
        try:
            # Get the text input widgets from ids
            email_phone = self.ids.get('email_phone_input')
            password = self.ids.get('password_input')
            
            if not email_phone or not password:
                print("Error: TextInput widgets not found")
                return False
                
            if not email_phone.text or not password.text:
                self.show_message('Error', 'Please fill in all fields')
                return False
                
            return True
        except Exception as e:
            print(f"Validation error: {e}")
            self.show_message('Error', 'An error occurred while validating input')
            return False
    
    def login(self):
        try:
            if not self.validate_input():
                return
            
            # Get the text input widgets from ids
            email_phone = self.ids.get('email_phone_input')
            password = self.ids.get('password_input')
            
            # Validate and proceed with login
            self.validate_and_proceed()
                
        except Exception as e:
            print(f"Login error: {e}")
            self.show_message('Error', 'An error occurred during login')
            # Reset password field on any error
            if 'password' in locals():
                password.text = ''
    
    def go_to_signup(self):
        try:
            # Navigate directly to email signup screen
            self.manager.current = 'email_signup'
        except Exception as e:
            print(f"Error navigating to signup: {e}")
            self.show_message('Error', 'Failed to navigate to signup screen')
    
    def on_leave(self):
        """Clean up when leaving the screen"""
        pass  # No need to close database as it's handled by the DatabaseService