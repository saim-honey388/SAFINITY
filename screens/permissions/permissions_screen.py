from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.metrics import dp
from kivy.clock import Clock
from kivy.properties import StringProperty

from utils.permission_handler import PermissionHandler

class PermissionsScreen(Screen):
    """Screen for handling app permissions"""
    
    location_permission = StringProperty('ASK_EVERY_TIME')
    contacts_permission = StringProperty('ASK_EVERY_TIME')
    storage_permission = StringProperty('ASK_EVERY_TIME')
    bluetooth_permission = StringProperty('ASK_EVERY_TIME')
    
    def __init__(self, **kwargs):
        super(PermissionsScreen, self).__init__(**kwargs)
        self.permission_handler = PermissionHandler()

    def on_enter(self):
        """Called when screen is entered"""
        # Check current permission status
        self.check_permissions()
    
    def check_permissions(self):
        """Check all permissions and update UI"""
        # Convert boolean to string values
        self.location_permission = 'ALLOWED' if self.permission_handler.check_location_permission() else 'NOT_ALLOWED'
        self.contacts_permission = 'ALLOWED' if self.permission_handler.check_contacts_permission() else 'NOT_ALLOWED'
        self.storage_permission = 'ALLOWED' if self.permission_handler.check_storage_permission() else 'NOT_ALLOWED'
        self.bluetooth_permission = 'ALLOWED' if self.permission_handler.check_bluetooth_permission() else 'NOT_ALLOWED'
    
    def show_permission_options(self, permission_type):
        """Show popup with permission options"""
        content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
        
        # Add title
        title = Label(
            text=f'{permission_type.replace("_", " ").title()} Permission',
            font_size='20sp',
            bold=True,
            color=(0.223, 0.510, 0.478, 1),
            size_hint_y=None,
            height=dp(40)
        )
        content.add_widget(title)
        
        # Add description
        description = Label(
            text='Choose how you want to allow this permission:',
            font_size='16sp',
            color=(0, 0, 0, 0.7),
            size_hint_y=None,
            height=dp(30)
        )
        content.add_widget(description)
        
        # Add options
        options = BoxLayout(orientation='vertical', spacing=dp(15))
        
        # Create popup first so we can reference it in the button callbacks
        popup = Popup(
            title='',
            content=content,
            size_hint=(None, None),
            size=(dp(300), dp(350)),
            background='',
            background_color=(1, 1, 1, 1),
            separator_height=0
        )
        
        # Allow all the time
        allow_all = Button(
            text='Allow all the time',
            size_hint_y=None,
            height=dp(50),
            background_normal='',
            background_color=(0.223, 0.510, 0.478, 1),
            color=(1, 1, 1, 1),
            font_size='16sp'
        )
        allow_all.bind(on_release=lambda x: self.handle_permission_choice(permission_type, 'ALLOW_ALL', popup))
        
        # Ask every time
        ask_every = Button(
            text='Ask every time',
            size_hint_y=None,
            height=dp(50),
            background_normal='',
            background_color=(0.223, 0.510, 0.478, 1),
            color=(1, 1, 1, 1),
            font_size='16sp'
        )
        ask_every.bind(on_release=lambda x: self.handle_permission_choice(permission_type, 'ASK_EVERY_TIME', popup))
        
        # Not allowed
        not_allowed = Button(
            text='Not allowed',
            size_hint_y=None,
            height=dp(50),
            background_normal='',
            background_color=(0.8, 0.2, 0.2, 1),
            color=(1, 1, 1, 1),
            font_size='16sp'
        )
        not_allowed.bind(on_release=lambda x: self.handle_permission_choice(permission_type, 'NOT_ALLOWED', popup))
        
        options.add_widget(allow_all)
        options.add_widget(ask_every)
        options.add_widget(not_allowed)
        content.add_widget(options)
        
        popup.open()

    def handle_permission_choice(self, permission_type, option, popup):
        """Handle permission choice and dismiss popup"""
        # Dismiss the popup immediately
        popup.dismiss()
        
        # Set the permission
        if option == 'ALLOW_ALL':
            success = self.request_permission(permission_type)
            if success:
                setattr(self, f"{permission_type}_permission", 'ALLOWED')
                self.show_quick_message(f"{permission_type.replace('_', ' ').title()} permission allowed")
            else:
                setattr(self, f"{permission_type}_permission", 'NOT_ALLOWED')
                self.show_quick_message(f"Failed to set {permission_type.replace('_', ' ').title()} permission", is_error=True)
        else:
            setattr(self, f"{permission_type}_permission", option)
            status = "will ask every time" if option == 'ASK_EVERY_TIME' else "not allowed"
            self.show_quick_message(f"{permission_type.replace('_', ' ').title()} permission {status}")

    def show_quick_message(self, message, is_error=False):
        """Show a quick message that automatically dismisses"""
        content = BoxLayout(orientation='vertical', padding=dp(20))
        content.add_widget(Label(
            text=message,
            color=(0.8, 0.2, 0.2, 1) if is_error else (0.223, 0.510, 0.478, 1)
        ))
        
        popup = Popup(
            title='',
            content=content,
            size_hint=(None, None),
            size=(dp(300), dp(150)),
            auto_dismiss=True,
            background='',
            background_color=(1, 1, 1, 1),
            separator_height=0
        )
        popup.open()
        
        # Auto dismiss after 1.5 seconds
        Clock.schedule_once(lambda dt: popup.dismiss(), 1.5)

    def request_permission(self, permission_type):
        """Request a specific permission"""
        try:
            if permission_type == 'location':
                return self.permission_handler.request_location_permission()
            elif permission_type == 'contacts':
                return self.permission_handler.request_contacts_permission()
            elif permission_type == 'storage':
                return self.permission_handler.request_storage_permission()
            elif permission_type == 'bluetooth':
                return self.permission_handler.request_bluetooth_permission()
        except Exception as e:
            print(f"Error requesting {permission_type} permission: {e}")
            return False
    
    def on_continue_press(self):
        """Handle continue button press"""
        self.manager.current = 'home'
