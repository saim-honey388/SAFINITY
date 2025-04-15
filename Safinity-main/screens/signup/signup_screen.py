from kivy.uix.screenmanager import Screen
from kivy.app import App
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from utils.database_service import DatabaseService
import traceback

class SignupScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db = DatabaseService()

    def validate_and_save(self, email, phone_number, password):
        """Validate and save signup data"""
        try:
            print(f"\n=== Signup Validation ===")
            print(f"Email: {email}")
            print(f"Phone: {phone_number}")
            
            # Create temp signup
            if self.db.create_temp_signup(email, phone_number, password, None):  # country will be added later
                print("Temp signup created successfully")
                self.manager.current = 'phone'
                return True
            else:
                print("Failed to create temp signup")
                return False
            
        except Exception as e:
            print(f"Error in validate_and_save: {str(e)}")
            traceback.print_exc()
            return False

    def validate_and_proceed(self, email, phone_number, password, confirm_password):
        """Validate signup data and proceed to next screen"""
        try:
            # Validate inputs
            if not email or not phone_number or not password or not confirm_password:
                self.show_error("Please fill in all fields")
                return

            if password != confirm_password:
                self.show_error("Passwords do not match")
                return

            if len(password) < 6:
                self.show_error("Password must be at least 6 characters long")
                return

            # Save to temporary signup table
            if self.db.save_temp_signup(email, phone_number, password, None):  # country will be added later
                print("Signup data saved successfully")
                # Store email/phone in app instance for later use
                app = App.get_running_app()
                app.signup_email = email
                app.signup_phone = phone_number
                # Proceed to flags screen
                self.manager.current = 'flags'
            else:
                print("Failed to save signup data")
                self.show_error("Email or phone number already exists")

        except Exception as e:
            print(f"Error in validate_and_proceed: {str(e)}")
            traceback.print_exc()
            self.show_error("An error occurred during signup")

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