from kivy.uix.screenmanager import Screen
from kivy.properties import BooleanProperty, ObjectProperty, NumericProperty
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.clock import Clock
from utils.database import SessionLocal, create_user, get_verified_user_by_phone, verify_user
from utils.twilio_service import send_verification_code, verify_code
from utils.phone_util import normalize_phone_number, find_phone_number_variants
from datetime import datetime
import re

class PhoneSignupScreen(Screen):
    phone_number = ObjectProperty(None)
    verification_code = ObjectProperty(None)
    verification_sent = BooleanProperty(False)
    countdown = NumericProperty(600)  # 10 minutes for Twilio Verify
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._verification_data = None
        self._timer_event = None
        self._db = SessionLocal()
        self._user_id = None
        self._phone_number = None  # Store phone number temporarily
        print("PhoneSignupScreen initialized")  # Debug print
    
    def on_enter(self):
        print("PhoneSignupScreen entered")  # Debug print
    
    def show_message(self, title, message):
        popup = Popup(
            title=title,
            content=Label(text=message, text_size=(280, None), halign='center'),
            size_hint=(None, None),
            size=(300, 200)
        )
        popup.open()
    
    def format_phone_number(self, phone):
        """
        Format phone number using the normalize_phone_number utility
        """
        try:
            # Use the new phone_util module to normalize the phone number
            normalized = normalize_phone_number(phone)
            
            # Ensure the number is valid (basic validation)
            if not normalized or len(normalized) < 10:
                raise ValueError("Phone number is too short")
                
            return normalized
        except Exception as e:
            print(f"Error formatting phone number: {str(e)}")
            raise ValueError("Invalid phone number format")
    
    def validate_phone(self):
        try:
            # Get the text input widgets from ids
            phone_input = self.ids.get('phone_number')
            
            if not phone_input:
                print("Error: Phone input widget not found")
                return False
                
            if not phone_input.text:
                self.show_message('Error', 'Please enter a phone number')
                return False
            
            try:
                formatted_phone = self.format_phone_number(phone_input.text)
                phone_input.text = formatted_phone
            except ValueError as e:
                self.show_message('Error', 'Please enter a valid phone number (e.g., +92336507022)')
                return False
                
            # Check if phone number is already registered and verified
            existing_user = get_verified_user_by_phone(self._db, phone_input.text)
            if existing_user:
                self.show_message('Error', 'Phone number already registered')
                return False
                
            return True
        except Exception as e:
            print(f"Phone validation error: {e}")
            self.show_message('Error', 'An error occurred while validating phone number')
            return False
    
    def start_resend_timer(self):
        self.countdown = 600  # 10 minutes for Twilio Verify
        if self._timer_event:
            self._timer_event.cancel()
        self._timer_event = Clock.schedule_interval(self._update_timer, 1)
    
    def _update_timer(self, dt):
        self.countdown -= 1
        if self.countdown <= 0:
            self._timer_event.cancel()
            self._timer_event = None
            return False
    
    def send_code(self):
        try:
            if not self.validate_phone():
                return
            
            # Get the text input widgets from ids
            phone_input = self.ids.get('phone_number')
            
            # Send verification code via Twilio Verify
            verification_data = send_verification_code(phone_input.text)
            if verification_data:
                self._verification_data = verification_data
                self._phone_number = phone_input.text  # Store phone number temporarily
                
                self.verification_sent = True
                self.start_resend_timer()
                self.show_message('Success', 'Verification code sent!')
            else:
                self.show_message('Error', 'Failed to send verification code')
        except Exception as e:
            print(f"Send code error: {e}")
            error_message = str(e)
            if "unverified" in error_message.lower():
                self.show_message(
                    'Error', 
                    'This phone number is not verified in Twilio. For testing, please use one of these numbers:\n'
                    '+14155552671\n'
                    '+14155552672\n'
                    '+14155552673\n'
                    '+14155552674\n'
                    '+14155552675\n\n'
                    'Or verify your number at:\n'
                    'https://www.twilio.com/console/phone-numbers/verified'
                )
            else:
                self.show_message('Error', 'An error occurred while sending verification code')
    
    def verify(self):
        try:
            # Get the text input widgets from ids
            phone_input = self.ids.get('phone_number')
            code_input = self.ids.get('verification_code')
            
            if not code_input or not code_input.text:
                self.show_message('Error', 'Please enter verification code')
                return
            
            if not self._verification_data:
                self.show_message('Error', 'Please request a new verification code')
                return
                
            # Verify the code using Twilio Verify
            if verify_code(phone_input.text, code_input.text):
                # Create user in database only after successful verification
                user = create_user(
                    self._db,
                    phone_number=phone_input.text
                )
                self._user_id = user.id
                
                self.show_message('Success', 'Phone number verified successfully!')
                # Clear inputs
                phone_input.text = ''
                code_input.text = ''
                self.verification_sent = False
                # Navigate to profile setup
                self.manager.current = 'profile_setup'
            else:
                self.show_message('Error', 'Invalid verification code')
        except Exception as e:
            print(f"Verification error: {e}")
            self.show_message('Error', 'An error occurred during verification')
    
    def back_to_signup_selection(self):
        # Clear any ongoing verification
        if self._timer_event:
            self._timer_event.cancel()
        self.verification_sent = False
        # Clear inputs
        phone_input = self.ids.get('phone_number')
        code_input = self.ids.get('verification_code')
        if phone_input:
            phone_input.text = ''
        if code_input:
            code_input.text = ''
        self._verification_data = None
        self._phone_number = None
        self._user_id = None
        self.manager.current = 'signup_selection'
    
    def on_leave(self):
        # Clean up database session
        self._db.close()