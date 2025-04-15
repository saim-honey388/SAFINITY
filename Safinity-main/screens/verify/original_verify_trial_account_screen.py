from kivy.uix.screenmanager import Screen
from kivy.properties import BooleanProperty, NumericProperty
from kivy.clock import Clock
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.app import App
from datetime import datetime
import os
from dotenv import load_dotenv
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

class VerifyScreen(Screen):
    resend_timer_active = BooleanProperty(False)
    countdown = NumericProperty(60)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.verification_code = None
        self.phone_number = None
        self.twilio_client = None
        self.verify_sid = None
        self.setup_twilio()

    def setup_twilio(self):
        """Initialize Twilio client with credentials"""
        try:
            load_dotenv()
            account_sid = os.getenv('TWILIO_ACCOUNT_SID')
            auth_token = os.getenv('TWILIO_AUTH_TOKEN')
            verify_sid = os.getenv('TWILIO_VERIFY_SERVICE_ID')
            
            if account_sid and auth_token and verify_sid:
                self.twilio_client = Client(account_sid, auth_token)
                self.verify_sid = verify_sid
                print("Twilio client initialized successfully in verify screen")
            else:
                print("Warning: Twilio credentials not found in .env file")
        except Exception as e:
            print(f"Error setting up Twilio in verify screen: {str(e)}")

    def verify_code(self):
        """Verify the entered code"""
        try:
            app = App.get_running_app()
            if not hasattr(app, 'phone_number'):
                self.show_message("Phone number not found")
                return

            # Get verification code from single input
            verification_code = self.ids.verification_code.text.strip()

            if len(verification_code) != 6:
                self.show_message("Please enter all 6 digits")
                return

            try:
                if not self.twilio_client:
                    print("Twilio client not initialized")
                    self.show_message("Service temporarily unavailable")
                    return

                # Check verification code
                verification_check = self.twilio_client.verify \
                    .v2 \
                    .services(self.verify_sid) \
                    .verification_checks \
                    .create(to=app.phone_number, code=verification_code)

                if verification_check.status == 'approved':
                    print("Verification successful")
                    # Navigate to profile setup screen
                    if 'profile_setup' not in self.manager.screen_names:
                        from screens.profile.profile_setup_screen import ProfileSetupScreen
                        self.manager.add_widget(ProfileSetupScreen(name='profile_setup'))
                    self.manager.current = 'profile_setup'
                else:
                    self.show_message("Invalid verification code")

            except TwilioRestException as e:
                print(f"Twilio verification error: {str(e)}")
                error_message = str(e)
                if "60200" in error_message:
                    self.show_message("Invalid verification code")
                elif "60202" in error_message:
                    self.show_message("Max check attempts reached")
                else:
                    self.show_message(f"Error: {str(e)}")

        except Exception as e:
            print(f"Error in verify_code: {str(e)}")
            self.show_message("An error occurred. Please try again.")

    def start_resend_timer(self):
        """Start the countdown timer for resend button"""
        self.resend_timer_active = True
        self.countdown = 60
        Clock.schedule_interval(self.update_countdown, 1)

    def update_countdown(self, dt):
        """Update the countdown timer"""
        self.countdown -= 1
        if self.countdown <= 0:
            self.resend_timer_active = False
            return False
        return True

    def resend_code(self):
        """Resend verification code"""
        if not self.resend_timer_active:
            try:
                app = App.get_running_app()
                verification = self.twilio_client.verify \
                    .v2 \
                    .services(self.verify_sid) \
                    .verifications \
                    .create(to=app.phone_number, channel='sms')
                
                if verification.status == 'pending':
                    self.show_message("New code sent")
                    self.start_resend_timer()
                    # Clear existing input
                    self.ids.verification_code.text = ''
                else:
                    self.show_message("Failed to send new code")
                    
            except Exception as e:
                print(f"Error resending code: {str(e)}")
                self.show_message("Failed to send new code")

    def show_message(self, message):
        """Show a popup message"""
        popup = Popup(
            title='',
            content=Label(text=message),
            size_hint=(None, None),
            size=(400, 200),
            background_color=(0.223, 0.510, 0.478, 1)
        )
        popup.open()

    def on_enter(self):
        """Called when screen is entered"""
        try:
            app = App.get_running_app()
            self.phone_number = app.phone_number
            
            # Send initial verification code
            if not self.resend_timer_active:
                try:
                    verification = self.twilio_client.verify \
                        .v2 \
                        .services(self.verify_sid) \
                        .verifications \
                        .create(to=self.phone_number, channel='sms')
                    
                    if verification.status == 'pending':
                        print(f"Initial verification code sent to: {self.phone_number}")
                        self.start_resend_timer()
                    else:
                        print(f"Failed to send initial verification code. Status: {verification.status}")
                        self.show_message("Failed to send verification code")
                except Exception as e:
                    print(f"Error sending initial verification code: {str(e)}")
                    self.show_message("Error sending verification code")
            
            # Clear any existing input
            self.ids.verification_code.text = ''
        except Exception as e:
            print(f"Error in on_enter: {str(e)}")
            self.show_message("Error initializing verification") 