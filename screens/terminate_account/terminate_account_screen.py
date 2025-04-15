from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.metrics import dp

from utils.database_service import DatabaseService
from utils.phone_util import normalize_phone_number, find_phone_number_variants
import hashlib


class TerminateAccountScreen(Screen):
    """Screen for account termination"""
    
    error_message = StringProperty("")
    
    def __init__(self, **kwargs):
        super(TerminateAccountScreen, self).__init__(**kwargs)
        self.db = DatabaseService()
        self.popup = None
    
    def on_enter(self):
        """Called when screen is entered"""
        # Clear previous inputs
        self.ids.phone_input.text = ""
        self.ids.password_input.text = ""
        self.error_message = ""
        
    def on_back_press(self, instance=None):
        """Return to home screen"""
        try:
            self.manager.current = 'home'
        except Exception as e:
            print(f"Error navigating back: {e}")
            # Fallback to login screen if home screen is not available
            self.manager.current = 'login'
    
    def show_error(self, message):
        """Display error message with animation"""
        self.error_message = message
        
        # Show error for 4 seconds then clear
        Clock.schedule_once(lambda dt: setattr(self, 'error_message', ""), 4)
        
        # Animate error message
        error_label = self.ids.error_label
        
        # Start with red background
        error_label.background_color = (0.8, 0.1, 0.1, 1)
        
        # Animate to make it noticeable
        anim = Animation(background_color=(0.8, 0.1, 0.1, 0.7), duration=0.5) + \
               Animation(background_color=(0.8, 0.1, 0.1, 1), duration=0.5)
        anim.repeat = True
        anim.start(error_label)
        
        # Stop animation after 4 seconds
        Clock.schedule_once(lambda dt: anim.cancel(error_label), 4)
    
    def show_confirmation(self):
        """Show confirmation popup before account termination"""
        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(20))
        
        # Warning message
        warning_label = Label(
            text="WARNING: This action cannot be undone!",
            color=(0.9, 0.1, 0.1, 1),
            bold=True,
            font_size=dp(18),
            size_hint_y=None,
            height=dp(40)
        )
        
        # Confirmation message
        confirm_label = Label(
            text="Are you sure you want to permanently delete your account? All your data will be lost.",
            halign='center',
            text_size=(dp(280), None),
            valign='middle',
            size_hint_y=None,
            height=dp(80)
        )
        
        # Buttons layout
        buttons = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        
        # Cancel button
        cancel_btn = Button(
            text="Cancel",
            background_color=(0.7, 0.7, 0.7, 1)
        )
        
        # Confirm button
        confirm_btn = Button(
            text="Delete Account",
            background_color=(0.8, 0.1, 0.1, 1)
        )
        
        # Add widgets to layout
        buttons.add_widget(cancel_btn)
        buttons.add_widget(confirm_btn)
        content.add_widget(warning_label)
        content.add_widget(confirm_label)
        content.add_widget(buttons)
        
        # Create and open popup
        self.popup = Popup(
            title="Confirm Account Termination",
            content=content,
            size_hint=(0.9, None),
            height=dp(250),
            auto_dismiss=False
        )
        
        # Bind button events
        cancel_btn.bind(on_release=self.popup.dismiss)
        confirm_btn.bind(on_release=self.confirm_termination)
        
        self.popup.open()
    
    def confirm_termination(self, instance):
        """Handle final account termination"""
        if self.popup:
            self.popup.dismiss()
        
        # Get app instance
        app = App.get_running_app()
        user_id = getattr(app, 'user_id', None)
        
        if not user_id:
            self.show_error("User ID not found. Please log in again.")
            return
        
        # Delete user from database
        success = self.db.delete_user(user_id)
        
        if success:
            # Show success message
            content = BoxLayout(orientation='vertical', padding=dp(20))
            msg = Label(
                text="Your account has been successfully deleted.\nThank you for using our service.",
                halign='center'
            )
            content.add_widget(msg)
            
            success_popup = Popup(
                title="Account Deleted",
                content=content,
                size_hint=(0.8, None),
                height=dp(200),
                auto_dismiss=False
            )
            
            # Create button to return to login
            btn = Button(
                text="Return to Login",
                size_hint=(0.7, None),
                height=dp(50),
                pos_hint={'center_x': 0.5}
            )
            content.add_widget(btn)
            
            # Bind button to close popup and go to login
            def on_btn_press(instance):
                success_popup.dismiss()
                # Clear user data
                app.clear_user_data()
                # Navigate to login screen
                self.manager.current = 'login'
            
            btn.bind(on_release=on_btn_press)
            success_popup.open()
        else:
            self.show_error("Failed to delete account. Please try again later.")
    
    def normalize_phone_number(self, phone):
        """
        Normalize a phone number to handle country codes
        
        Args:
            phone: The phone number to normalize
            
        Returns:
            The normalized phone number for comparison
        """
        # Use the standardized phone utility
        return normalize_phone_number(phone)

    def attempt_termination(self):
        """Validate credentials and attempt account termination"""
        # Get inputs
        phone = self.ids.phone_input.text.strip()
        password = self.ids.password_input.text.strip()
        
        # Validate inputs
        if not phone:
            self.show_error("Please enter your phone number")
            return
        
        if not password:
            self.show_error("Please enter your password")
            return
        
        # Get user data
        app = App.get_running_app()
        user_id = getattr(app, 'user_id', None) or app.read_user_data().get('user_id')
        
        if not user_id:
            self.show_error("User ID not found. Please log in again.")
            return
        
        # Get user from database
        user_data = self.db.get_user_by_id(user_id)
        
        if not user_data:
            self.show_error("User not found. Please log in again.")
            return
        
        print(f"Validating termination request for user {user_id}")
        
        # Normalize phone numbers for comparison
        input_phone = self.normalize_phone_number(phone)
        stored_phone = self.normalize_phone_number(user_data.get('phone_number', ''))
        
        print(f"Comparing phones - Input: {input_phone}, Stored: {stored_phone}")
        
        # Try to match with possible phone number variants
        if input_phone != stored_phone:
            # Generate phone variants and check if any match
            input_variants = find_phone_number_variants(phone)
            stored_variants = find_phone_number_variants(user_data.get('phone_number', ''))
            
            print(f"Input variants: {input_variants}")
            print(f"Stored variants: {stored_variants}")
            
            # Check if any variant matches
            match_found = False
            for input_var in input_variants:
                if input_var in stored_variants:
                    print(f"Match found with variant: {input_var}")
                    match_found = True
                    break
            
            if not match_found:
                self.show_error("Phone number does not match your account")
                return
        
        # Hash password for comparison
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        # Compare with stored password
        if user_data.get('password') != hashed_password:
            self.show_error("Incorrect password")
            return
        
        # If we get here, credentials are valid
        print("User credentials verified, showing confirmation dialog")
        self.show_confirmation()
