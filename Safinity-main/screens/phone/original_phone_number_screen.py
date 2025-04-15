from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.app import App
from twilio.rest import Client
import os
from dotenv import load_dotenv
import re
from twilio.base.exceptions import TwilioRestException

class PhoneNumberScreen(Screen):
    selected_country_code = StringProperty('')
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.twilio_client = None
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
                print("Twilio client initialized successfully")
            else:
                print("Warning: Twilio credentials not found in .env file")
        except Exception as e:
            print(f"Error setting up Twilio: {str(e)}")

    def on_enter(self):
        """Called when screen is entered"""
        try:
            app = App.get_running_app()
            if hasattr(app, 'country_code'):
                self.selected_country_code = app.country_code
                if self.ids.get('country_code'):
                    self.ids.country_code.text = f"+{app.country_code}"
        except Exception as e:
            print(f"Error in on_enter: {str(e)}")

    def validate_and_send_code(self):
        """Validate phone number and send verification code"""
        try:
            # Get the phone number from input
            phone_number = self.ids.phone_input.text.strip()
            
            # Get country code from app
            app = App.get_running_app()
            country_code = app.country_code if hasattr(app, 'country_code') else ''
            
            if not phone_number:
                self.show_message("Please enter your phone number")
                return
                
            # Remove any non-digit characters
            phone_number = ''.join(filter(str.isdigit, phone_number))
            
            # Format the phone number with country code
            formatted_number = f"+{country_code}{phone_number}"
            print(f"Sending verification code to: {formatted_number}")
            
            # Basic validation
            if len(phone_number) < 8:
                self.show_message("Please enter a valid phone number")
                return
                
            try:
                if not self.twilio_client:
                    print("Twilio client not initialized")
                    self.show_message("Service temporarily unavailable")
                    return
                    
                # Send verification code using Twilio Verify
                verification = self.twilio_client.verify \
                    .v2 \
                    .services(self.verify_sid) \
                    .verifications \
                    .create(to=formatted_number, channel='sms')
                    
                print(f"Verification status: {verification.status}")
                
                if verification.status == 'pending':
                    # Store the phone number for verification
                    app.phone_number = formatted_number
                    
                    # Navigate to verify screen
                    if 'verify' not in self.manager.screen_names:
                        from screens.verify.verify_screen import VerifyScreen
                        self.manager.add_widget(VerifyScreen(name='verify'))
                    self.manager.current = 'verify'
                else:
                    self.show_message("Error sending verification code. Please try again.")
                    
            except TwilioRestException as e:
                print(f"Twilio error: {str(e)}")
                error_message = str(e)
                if "60200" in error_message:  # Invalid parameter
                    self.show_message("Invalid phone number format")
                elif "60203" in error_message:  # Max send attempts reached
                    self.show_message("Too many attempts. Please try again later")
                else:
                    self.show_message(f"Error: {str(e)}")
                    
            except Exception as e:
                print(f"Error sending verification code: {str(e)}")
                self.show_message("Error sending verification code. Please try again.")
                
        except Exception as e:
            print(f"Error in validate_and_send_code: {str(e)}")
            self.show_message("An error occurred. Please try again.")

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
 