from kivy.uix.screenmanager import Screen
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.core.window import Window
from kivy.properties import ObjectProperty
from kivy.uix.popup import Popup
from utils.database import SessionLocal, get_user_by_id

class WelcomeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._db = SessionLocal()
        self._user_id = None
        print("WelcomeScreen initialized")
        self.setup_ui()
    
    def setup_ui(self):
        # Create main layout
        layout = BoxLayout(orientation='vertical', padding=20, spacing=20)
        
        # Add logo or welcome image
        logo = Image(
            source='assets/logo.png' if hasattr(self, 'assets/logo.png') else '',
            size_hint=(None, None),
            size=(200, 200),
            pos_hint={'center_x': 0.5}
        )
        layout.add_widget(logo)
        
        # Add welcome text
        welcome_label = Label(
            text='Welcome to Safinity',
            font_size='24sp',
            size_hint_y=None,
            height='50dp'
        )
        layout.add_widget(welcome_label)
        
        # Add description
        desc_label = Label(
            text='Your Personal Safety Companion',
            font_size='16sp',
            size_hint_y=None,
            height='30dp'
        )
        layout.add_widget(desc_label)
        
        # Add buttons
        login_button = Button(
            text='Login',
            size_hint=(None, None),
            size=(200, 50),
            pos_hint={'center_x': 0.5}
        )
        login_button.bind(on_press=self.go_to_login)
        layout.add_widget(login_button)
        
        signup_button = Button(
            text='Sign Up',
            size_hint=(None, None),
            size=(200, 50),
            pos_hint={'center_x': 0.5}
        )
        signup_button.bind(on_press=self.go_to_signup)
        layout.add_widget(signup_button)
        
        self.add_widget(layout)
    
    def go_to_login(self, instance):
        self.manager.current = 'login'
    
    def go_to_signup(self, instance):
        self.manager.current = 'signup_selection'

    def on_enter(self):
        print("WelcomeScreen entered")
        # Get user_id from the previous screen
        if hasattr(self.manager.get_screen('login'), '_user_id'):
            self._user_id = self.manager.get_screen('login')._user_id
        elif hasattr(self.manager.get_screen('profile_setup'), '_user_id'):
            self._user_id = self.manager.get_screen('profile_setup')._user_id

        if self._user_id:
            user = get_user_by_id(self._db, self._user_id)
            if user:
                welcome_text = f"Welcome, {user.first_name}!"
                if hasattr(self, 'welcome_label'):
                    self.welcome_label.text = welcome_text
        else:
            self.manager.current = 'login'

    def logout(self):
        # Clear user ID from all screens
        if hasattr(self.manager.get_screen('login'), '_user_id'):
            delattr(self.manager.get_screen('login'), '_user_id')
        if hasattr(self.manager.get_screen('profile_setup'), '_user_id'):
            delattr(self.manager.get_screen('profile_setup'), '_user_id')
        if hasattr(self.manager.get_screen('phone_signup'), '_user_id'):
            delattr(self.manager.get_screen('phone_signup'), '_user_id')
        
        # Navigate to login screen
        self.manager.current = 'login'

    def on_leave(self):
        self._db.close() 