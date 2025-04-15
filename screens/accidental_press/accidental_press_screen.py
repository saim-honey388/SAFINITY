from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty
from kivy.app import App
from utils.database_service import DatabaseService
from utils.emergency_contact_service import EmergencyContactService
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.clock import Clock

class AccidentalPressScreen(Screen):
    """Screen for verifying accidental emergency button press"""
    
    status_message = StringProperty('')
    
    def __init__(self, **kwargs):
        super(AccidentalPressScreen, self).__init__(**kwargs)
        self.db = DatabaseService()
        self.emergency_service = EmergencyContactService()
    
    def on_enter(self):
        """Called when screen is entered"""
        self.status_message = 'Please verify your identity to confirm accidental press'
        # Reset input fields
        self.ids.password_input.text = ''
        self.ids.phone_input.text = ''
    
    def verify_user(self):
        """Verify user credentials and send accidental press message"""
        password = self.ids.password_input.text.strip()
        phone = self.ids.phone_input.text.strip()
        
        if not password or not phone:
            self.show_error('Please enter both password and phone number')
            return
        
        # Get app instance to access user data
        app = App.get_running_app()
        user_id = getattr(app, 'user_id', None)
        
        if not user_id:
            self.show_error('User not logged in')
            return
        
        # Verify user credentials
        session = self.db.get_session()
        try:
            user = self.db.verify_user_credentials(session, phone, password)
            
            if not user or user.id != user_id:
                self.show_error('Invalid credentials')
                return
            
            # Send accidental press message
            self.status_message = 'Sending accidental press notification...'
            self.send_accidental_press_message(session, user_id)
            
        finally:
            session.close()
    
    def send_accidental_press_message(self, session, user_id):
        """Send accidental press message to emergency contacts"""
        # Custom message for accidental press
        def send_message():
            result = self.emergency_service.send_custom_message(
                session, 
                user_id,
                "Accidental Press : The previous emergency alert was triggered by mistake. No action is required. The user is safe"
            )
            
            if result['status'] in ['success', 'partial']:
                self.show_success('Accidental press notification sent')
                # Return to home screen after delay
                Clock.schedule_once(lambda dt: self.go_to_home(), 2)
            else:
                self.show_error(f"Failed to send notification: {result['message']}")
        
        # Use Clock to avoid blocking UI
        Clock.schedule_once(lambda dt: send_message(), 0.5)
    
    def show_error(self, message):
        """Show error popup"""
        self.status_message = message
        popup = Popup(title='Error',
                     content=Label(text=message),
                     size_hint=(0.8, 0.4))
        popup.open()
    
    def show_success(self, message):
        """Show success popup"""
        self.status_message = message
        popup = Popup(title='Success',
                     content=Label(text=message),
                     size_hint=(0.8, 0.4))
        popup.open()
    
    def go_to_home(self):
        """Navigate back to home screen"""
        self.manager.current = 'home'
    
    def on_back_press(self):
        """Handle back button press"""
        self.go_to_home()