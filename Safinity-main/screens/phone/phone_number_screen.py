from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.app import App
import os
from dotenv import load_dotenv
import re
import traceback
from utils.database_service import DatabaseService
from utils.veevotech_service import VeevotechService

class PhoneNumberScreen(Screen):
    selected_country_code = StringProperty('')
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db = DatabaseService()
        self.veevotech = VeevotechService()

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
            print(traceback.format_exc())

    def validate_and_send_code(self):
        """Validate phone number and send verification code"""
        try:
            print("\n=== Phone Number Validation ===")
            
            # Get the entered phone number
            phone_input = self.ids.phone_input.text.strip()
            country_code = self.selected_country_code
            
            if not phone_input or not country_code:
                print("Error: Phone input or country code is empty")
                self.show_error("Please enter a valid phone number")
                return
            
            # Format phone number with country code
            phone_number = f"+{country_code}{phone_input}"
            print(f"Phone number: {phone_number}")
            
            # Get app instance to access stored data
            app = App.get_running_app()
            email = getattr(app, 'email', None)
            password = getattr(app, 'password', None)
            country = getattr(app, 'selected_country', None)
            
            print("\nApp instance data:")
            print(f"- Email: {email}")
            print(f"- Password: {'Yes' if password else 'No'}")
            print(f"- Country: {country}")
            
            # Validate required fields
            if not email or not password:
                print("Error: Missing required fields")
                print(f"- Email: {email}")
                print(f"- Password: {'Yes' if password else 'No'}")
                self.show_error("Please complete email signup first")
                # Go back to email signup screen
                self.manager.current = 'email_signup'
                return
            
            # Create or update temp signup
            temp_signup, error = self.db.create_temp_signup(
                email=email,
                phone_number=phone_number,
                password=password,
                country=country
            )
            
            if error:
                print(f"Error creating temp signup: {error}")
                if error == "USER_EXISTS_EMAIL":
                    self.show_error("Email already registered. Please sign up with a different email.")
                    self.manager.current = 'email_signup'
                elif error == "USER_EXISTS_PHONE":
                    self.show_error("Phone number already registered. Please sign up with a different phone number.")
                    self.manager.current = 'email_signup'
                else:
                    self.show_error(error)
                return
            
            if not temp_signup:
                print("Failed to create temp signup")
                self.show_error("Failed to create temporary signup")
                return
            
            print("Created/Updated temp signup successfully")
            
            # Store data in app instance
            app.phone_number = phone_number
            app.country_code = country_code
            
            # Send verification code
            self.send_verification_code(phone_number)
            
            # Navigate to verify screen
            self.manager.current = 'verify'
            
        except Exception as e:
            print(f"Error in validate_and_send_code: {str(e)}")
            traceback.print_exc()
            self.show_error("An error occurred while validating phone number")
            
    def send_verification_code(self, phone_number):
        """Send verification code using the configured service"""
        try:
            # Use VeevotechService to send verification code
            success = self.veevotech.send_verification_code(phone_number)
            if success:
                print(f"Verification code sent to {phone_number}")
                self.show_message(f"Verification code sent to {phone_number}")
            else:
                print("Failed to send verification code")
                self.show_error("Failed to send verification code")
        except Exception as e:
            print(f"Error sending verification code: {str(e)}")
            traceback.print_exc()
            self.show_error("Failed to send verification code")

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
        """Show a popup message"""
        popup = Popup(
            title='',
            content=Label(text=message),
            size_hint=(None, None),
            size=(400, 200),
            background_color=(0.223, 0.510, 0.478, 1)
        )
        popup.open()
 