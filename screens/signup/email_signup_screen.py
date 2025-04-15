from kivy.uix.screenmanager import Screen
from kivy.properties import BooleanProperty, NumericProperty, ObjectProperty
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.app import App
#from firebase.firebase_config import send_email_verification, verify_email_code, create_user_with_email
import re
import traceback

class EmailSignupError(Exception):
    """Custom exception for email signup operations"""
    pass

class EmailSignupScreen(Screen):
    # Define widget properties
    email_input = ObjectProperty(None)
    password_input = ObjectProperty(None)
    confirm_password_input = ObjectProperty(None)
    
    # State properties
    verification_sent = BooleanProperty(False)
    countdown = NumericProperty(0)
    _timer_event = None
    
    def __init__(self, **kwargs):
        try:
            super(EmailSignupScreen, self).__init__(**kwargs)
            self._timer_event = None
            print("EmailSignupScreen initialized")
            Clock.schedule_once(self._init_ui, 0)
        except Exception as e:
            print(f"Error initializing EmailSignupScreen: {str(e)}")
            print(traceback.format_exc())
    
    def _init_ui(self, dt):
        """Initialize UI elements after kv file is loaded"""
        try:
            print("Initializing EmailSignupScreen UI")
            # Clear any existing input
            if hasattr(self.ids, 'email_input'):
                self.ids.email_input.text = ''
            if hasattr(self.ids, 'password_input'):
                self.ids.password_input.text = ''
            if hasattr(self.ids, 'confirm_password_input'):
                self.ids.confirm_password_input.text = ''
        except Exception as e:
            print(f"Error in _init_ui: {str(e)}")
            print(traceback.format_exc())
    
    def show_message(self, message):
        """Show a popup message to the user"""
        try:
            app = App.get_running_app()
            if hasattr(app, 'show_message'):
                app.show_message(message)
            else:
                print(f"Message to user: {message}")
        except Exception as e:
            print(f"Error showing message: {str(e)}")
            print(f"Message was: {message}")
            print(traceback.format_exc())
    
    def validate_email(self, email):
        """Validate email format"""
        try:
            if not email:
                raise EmailSignupError("Please enter your email address")
            
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, email):
                raise EmailSignupError("Please enter a valid email address")
            
            return True
        except EmailSignupError as e:
            self.show_message(str(e))
            return False
        except Exception as e:
            print(f"Error validating email: {str(e)}")
            print(traceback.format_exc())
            self.show_message("Error validating email")
            return False
    
    def validate_password(self, password, confirm_password):
        """Validate password requirements"""
        try:
            if not password:
                raise EmailSignupError("Please enter a password")
            
            if len(password) < 6:
                raise EmailSignupError("Password must be at least 6 characters long")
            
            if password != confirm_password:
                raise EmailSignupError("Passwords do not match")
            
            return True
        except EmailSignupError as e:
            self.show_message(str(e))
            return False
        except Exception as e:
            print(f"Error validating password: {str(e)}")
            print(traceback.format_exc())
            self.show_message("Error validating password")
            return False
    
    def validate_and_signup(self):
        """Validate the email and create a new user account"""
        try:
            print("Starting validation...")
            email = self.ids.email_input.text
            password = self.ids.password_input.text
            confirm_password = self.ids.confirm_password_input.text
            
            print(f"Validating email: {email}")
            if not self.validate_email(email):
                return
                
            print("Validating password...")
            if not self.validate_password(password, confirm_password):
                return
                
            print("Creating user account...")
            app = App.get_running_app()
            
            # Store signup data in app instance with correct variable names
            app.email = email  # Changed from signup_email
            app.password = password  # Changed from signup_password
            print(f"Stored signup data in app instance:")
            print(f"- Email: {email}")
            print(f"- Password: {'Yes' if password else 'No'}")
            
            print("Navigating to flags screen...")
            # Add the flags screen if it doesn't exist
            if 'flags_screen' not in self.manager.screen_names:
                from screens.flags.flags_screen import FlagsScreen
                flags_screen = FlagsScreen(name='flags_screen')
                self.manager.add_widget(flags_screen)
            
            self.manager.current = 'flags_screen'
            
        except Exception as e:
            print(f"Error in validate_and_signup: {str(e)}")
            traceback.print_exc()
            self.show_message("Error creating account")
    
    def start_resend_timer(self):
        self.countdown = 60
        if self._timer_event:
            self._timer_event.cancel()
        self._timer_event = Clock.schedule_interval(self._update_timer, 1)
    
    def _update_timer(self, dt):
        """Update countdown timer"""
        try:
            if self.countdown > 0:
                self.countdown -= 1
            elif self._timer_event:
                self._timer_event.cancel()
                self._timer_event = None
        except Exception as e:
            print(f"Error in _update_timer: {str(e)}")
            if self._timer_event:
                self._timer_event.cancel()
                self._timer_event = None
    
    def send_code(self):
        if not self.validate_email():
            return
        
        try:
            verification_id = send_email_verification(self.email.text)
            if verification_id:
                self._verification_id = verification_id
                self.verification_sent = True
                self.start_resend_timer()
                self.show_message('Verification code sent to your email!')
            else:
                self.show_message('Failed to send verification code')
        except Exception as e:
            self.show_message(str(e))
    
    def verify(self):
        if not self.verification_code.text:
            self.show_message('Please enter verification code')
            return
        
        try:
            if verify_email_code(self._verification_id, self.verification_code.text):
                # Create user account
                user = create_user_with_email(self.email.text)
                if user:
                    self.show_message('Account created successfully!')
                    # Clear inputs
                    self.email.text = ''
                    self.verification_code.text = ''
                    self.verification_sent = False
                    # Navigate to profile setup
                    self.manager.current = 'profile_setup'
                else:
                    self.show_message('Failed to create account')
            else:
                self.show_message('Invalid verification code')
        except Exception as e:
            self.show_message(str(e))
    
    def back_to_signup_selection(self):
        # Clear any ongoing verification
        if self._timer_event:
            self._timer_event.cancel()
        self.verification_sent = False
        self.email.text = ''
        self.verification_code.text = ''
        self.manager.current = 'signup_selection'

    def on_enter(self):
        """Called when the screen is entered"""
        try:
            print("Entering email signup screen")
            # Clear any existing input
            if hasattr(self.ids, 'email_input'):
                self.ids.email_input.text = ''
            if hasattr(self.ids, 'password_input'):
                self.ids.password_input.text = ''
            if hasattr(self.ids, 'confirm_password_input'):
                self.ids.confirm_password_input.text = ''
        except Exception as e:
            print(f"Error in on_enter: {str(e)}")
            print(traceback.format_exc())

    def on_leave(self):
        """Clean up resources when leaving the screen."""
        self._cancel_timer()

    def back_to_login(self):
        """Navigate back to the login screen."""
        self.manager.transition.direction = 'right'
        self.manager.current = 'login'

    def _cancel_timer(self):
        """Cancel any ongoing timer"""
        try:
            if self._timer_event:
                self._timer_event.cancel()
                self._timer_event = None
        except Exception as e:
            print(f"Error in _cancel_timer: {str(e)}")
            if self._timer_event:
                self._timer_event.cancel()
                self._timer_event = None 