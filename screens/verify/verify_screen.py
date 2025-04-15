from kivy.uix.screenmanager import Screen
from kivy.properties import BooleanProperty, NumericProperty, StringProperty
from kivy.clock import Clock
from kivy.app import App
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from utils.veevotech_service import VeevotechService
from utils.database_service import DatabaseService
from utils.phone_util import normalize_phone_number, find_phone_number_variants
from models.database_models import User
import traceback

class VerifyScreen(Screen):
    resend_timer_active = BooleanProperty(False)
    countdown = NumericProperty(60)
    phone_number = StringProperty('')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.countdown_event = None
        self.veevotech = VeevotechService()
        self.db = DatabaseService()

    def on_enter(self):
        """Called when the screen is entered"""
        try:
            app = App.get_running_app()
            if hasattr(app, 'phone_number'):
                # Normalize the phone number
                self.phone_number = normalize_phone_number(app.phone_number)
                print(f"Phone number set and normalized: {self.phone_number}")
                # Send initial verification code
                self.send_verification_code()
            else:
                print("Warning: No phone number found in app")
                self.show_error("No phone number found")
        except Exception as e:
            print(f"Error in on_enter: {str(e)}")
            traceback.print_exc()
            self.show_error("Failed to initialize verification")

    def send_verification_code(self):
        """Send verification code"""
        try:
            response = self.veevotech.send_verification_code(self.phone_number)
            if response['status'] == 'pending':
                print("Verification code sent successfully")
                self.start_countdown()
            else:
                print(f"Failed to send verification code: {response['message']}")
                self.show_error(response['message'])
        except Exception as e:
            print(f"Error sending verification code: {str(e)}")
            traceback.print_exc()
            self.show_error("Failed to send verification code")

    def verify_code_input(self, code=None):
        """Verify the entered verification code"""
        try:
            print("\n=== Verifying Code ===")
            
            # Get code from input field if not provided
            if code is None:
                code = self.ids.verification_code.text.strip()
            
            if not code:
                self.show_error("Please enter the verification code")
                return
            
            print(f"Verifying code: {code}")
            
            # Get temp signup data
            temp_data = self.db.get_temp_signup()
            if not temp_data:
                self.show_error("No verification data found")
                return
            
            print(f"Temp signup data:")
            print(f"- Email: {temp_data.get('email')}")
            print(f"- Phone: {temp_data.get('phone_number')}")
            print(f"- Country: {temp_data.get('country')}")
            
            # Check if any user exists with the same email or phone in users table
            existing_user = self.db.session.query(User).filter(
                (User.email == temp_data.get('email')) | 
                (User.phone_number == temp_data.get('phone_number'))
            ).first()
            
            if existing_user:
                print("Found existing user:")
                print(f"- Email: {existing_user.email}")
                print(f"- Phone: {existing_user.phone_number}")
                
                # Delete temp signup since user already exists
                self.db.delete_temp_signup()
                
                # Show appropriate error message
                if existing_user.email == temp_data.get('email'):
                    self.show_error("An account already exists with this email")
                else:
                    self.show_error("An account already exists with this phone number")
                
                # Go back to email screen instead of signup
                self.manager.current = 'email'
                return
            
            # If no existing user found, move data to users table
            success, message = self.db.move_basic_data_to_users(
                email=temp_data.get('email'),
                phone_number=temp_data.get('phone_number'),
                password=temp_data.get('password'),
                country=temp_data.get('country')
            )
            
            if success:
                print("Basic data moved successfully")
                # Store verified phone number in app instance
                app = App.get_running_app()
                app.verified_phone_number = temp_data.get('phone_number')
                app.email = temp_data.get('email')  # Also store email
                
                # Navigate to profile setup
                self.manager.current = 'profile_setup'
            else:
                print(f"Error: {message}")
                self.show_error(message)
                
        except Exception as e:
            print(f"Error in verify_code_input: {str(e)}")
            traceback.print_exc()
            self.show_error("An error occurred during verification")

    def verification_successful(self):
        """Handle successful verification"""
        try:
            print("Verification successful - transitioning to profile setup")
            app = App.get_running_app()
            if hasattr(app, 'phone_number'):
                app.verified_phone_number = app.phone_number
            self.manager.current = 'profile_setup'
        except Exception as e:
            print(f"Error in verification_successful: {str(e)}")
            traceback.print_exc()
            self.show_error("Failed to complete verification")

    def resend_code(self):
        """Resend verification code"""
        try:
            if self.resend_timer_active:
                print("Resend timer still active")
                remaining = max(0, self.countdown)
                self.show_message(f"Please wait {remaining} seconds before requesting a new code")
                return

            # Send new verification code
            self.send_verification_code()
                
        except Exception as e:
            print(f"Error in resend_code: {str(e)}")
            traceback.print_exc()
            self.show_error("Failed to resend code")

    def start_countdown(self):
        """Start the countdown timer for resend button"""
        self.resend_timer_active = True
        self.countdown = 60
        if self.countdown_event:
            self.countdown_event.cancel()
        self.countdown_event = Clock.schedule_interval(self.update_countdown, 1)
        self.ids.resend_button.text = f"Resend ({self.countdown}s)"

    def update_countdown(self, dt):
        """Update the countdown timer"""
        self.countdown -= 1
        self.ids.resend_button.text = f"Resend ({self.countdown}s)"
        
        if self.countdown <= 0:
            self.resend_timer_active = False
            self.ids.resend_button.text = "Resend Code"
            if self.countdown_event:
                self.countdown_event.cancel()
            return False

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

    def show_message(self, message):
        """Show an informational message popup"""
        popup = Popup(
            title='Info',
            content=Label(
                text=message,
                color=(1, 1, 1, 1)
            ),
            size_hint=(None, None),
            size=(300, 150),
            background_color=(0.223, 0.510, 0.478, 1)
        )
        popup.open()

    def on_leave(self):
        """Clean up when leaving the screen"""
        if self.countdown_event:
            self.countdown_event.cancel()
