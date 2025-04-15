from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty, BooleanProperty, StringProperty
from kivy.app import App
from utils.database_service import DatabaseService
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.animation import Animation
from kivy.uix.boxlayout import BoxLayout
from kivy.metrics import dp
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
import os
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.button import Button
from kivy.uix.relativelayout import RelativeLayout
from kivy.utils import platform
from kivy.uix.modalview import ModalView
from kivy.uix.widget import Widget
from kivy.clock import Clock
import traceback
from utils.bluetooth_service import BluetoothService
from utils.emergency_contact_service import EmergencyContactService

class SliderMenu(BoxLayout):
    profile_picture = StringProperty('assets/profile_icon.png')  # Default profile picture
    user_name = StringProperty('User Name')  # Default user name
    
    def __init__(self, **kwargs):
        super(SliderMenu, self).__init__(**kwargs)
        Clock.schedule_once(self.init_ui, 0.1)
        
    def init_ui(self, dt):
        """Initialize UI elements"""
        self.check_profile_data()
        
        # Start off-screen to the left
        self.pos_hint = {'x': -1, 'top': 1}
        # Take up 80% of screen width
        self.size_hint = (0.4, 1)
        # Set background color
        with self.canvas.before:
            Color(60/255, 60/255, 60/255, 0.7)  # Light gray background
            self.rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_rect, size=self._update_rect)
        
    def _update_rect(self, instance, value):
        """Update the rectangle position and size when the widget changes"""
        self.rect.pos = self.pos
        self.rect.size = self.size
        
    def check_profile_data(self):
        """Check and load profile data from database or app data"""
        try:
            app = App.get_running_app()
            user_data = app.read_user_data()
            
            print(f"Checking profile data, user_data: {user_data}")
            
            # Check if user_data is None before trying to access its attributes
            if user_data is None:
                print("No user data available")
                return
                
            # Check if profile picture path is stored in app data
            profile_pic = user_data.get('profile_picture')
            if profile_pic and os.path.exists(profile_pic):
                try:
                    # Try to load the image, if it fails, use default
                    from kivy.core.image import Image as CoreImage
                    CoreImage(profile_pic)
                    self.profile_picture = profile_pic
                    print(f"Loading profile picture from: {profile_pic}")
                except Exception as e:
                    print(f"Error loading profile picture: {str(e)}")
                    self.profile_picture = 'assets/profile_icon.png'
            
            # Try to get user info from database
            # Try first with app.user_id property
            user_id = None
            if hasattr(app, 'user_id') and app.user_id:
                user_id = app.user_id
                print(f"Using user ID from app property: {user_id}")
            else:
                # Fallback to user_id in user_data
                user_id = user_data.get('user_id')
                print(f"Using user ID from user_data: {user_id}")
            
            if user_id:
                # Query database for user info
                db = DatabaseService()
                print(f"Querying database for user with ID: {user_id}")
                db_user = db.get_user_info(user_id)
                
                if db_user:
                    print(f"Found user in database: {db_user}")
                    # Update user name if available
                    if db_user.get('full_name'):
                        self.user_name = db_user.get('full_name')
                        print(f"User name set from database: {self.user_name}")
                        
                    # Update profile picture if available and path exists
                    if db_user.get('profile_picture') and os.path.exists(db_user.get('profile_picture')):
                        try:
                            # Try to load the image, if it fails, use default
                            from kivy.core.image import Image as CoreImage
                            CoreImage(db_user.get('profile_picture'))
                            self.profile_picture = db_user.get('profile_picture')
                            print(f"Profile picture set from database: {self.profile_picture}")
                        except Exception as e:
                            print(f"Error loading profile picture from database: {str(e)}")
                            self.profile_picture = 'assets/profile_icon.png'
                else:
                    print(f"No user found in database with ID: {user_id}")
            else:
                print("No user ID available, couldn't query database")
                
                # If we have the name in app data, use that
                if user_data.get('full_name'):
                    self.user_name = user_data.get('full_name')
                    print(f"Using name from app data: {self.user_name}")
            
            print(f"Profile check complete. Using name: {self.user_name}, picture: {self.profile_picture}")
        except Exception as e:
            print(f"Error loading profile data: {str(e)}")
            traceback.print_exc()
    
    def update_profile_picture(self, *args):
        """Open file chooser to update profile picture
        
        This function is called when either the profile picture or the plus button is clicked.
        We need to determine which one was clicked and only proceed if it was the plus button.
        """
        print("Update profile picture clicked")
        app = App.get_running_app()
        
        # Check storage permission first
        if not app.check_permission('storage'):
            app.request_permission('storage', callback=self._after_permission_check)
            return
            
        self._show_file_chooser()
    
    def _after_permission_check(self, permission, granted):
        """Called after permission check"""
        print(f"Permission check result for {permission}: {granted}")
        if granted and permission == 'storage':
            self._show_file_chooser()
        else:
            print("Storage permission denied, cannot update profile picture")
    
    def _show_file_chooser(self):
        """Show file chooser dialog"""
        print("Showing file chooser")
        parent = self.parent
        if parent and hasattr(parent, 'show_file_chooser'):
            parent.show_file_chooser()
    
    def slide_in(self):
        """Animate the slider menu to slide in"""
        self.check_profile_data()  # Update profile data when menu opens
        # Ensure the menu is positioned correctly before animation
        self.pos_hint.update({'top': 1})
        anim = Animation(pos_hint={'x': 0, 'top': 1}, duration=0.3, t='out_cubic')
        anim.start(self)
        # Force update of children layout
        Clock.schedule_once(lambda dt: self.do_layout(), 0.1)
    
    def slide_out(self):
        """Animate the slider menu to slide out"""
        anim = Animation(pos_hint={'x': -1, 'top': 1}, duration=0.3, t='out_cubic')
        anim.start(self)

class HomeScreen(Screen):
    slider_menu = ObjectProperty(None)
    slider_open = BooleanProperty(False)
    bluetooth_status = StringProperty('Disconnected')
    
    def __init__(self, **kwargs):
        print("Initializing HomeScreen...")
        super().__init__(**kwargs)
        self.db = DatabaseService()
        self.bluetooth_service = BluetoothService()
        self.emergency_service = EmergencyContactService()
        print(f"HomeScreen initialized with name: {self.name}")
        print(f"HomeScreen parent: {self.parent}")

    def on_enter(self):
        print("HomeScreen entered")
        app = App.get_running_app()
        user_identifier = getattr(app, 'user_identifier', None)
        print(f"Current user: {user_identifier}")
        print(f"Available screens: {self.manager.screen_names if self.manager else 'No manager'}")
        print(f"Current screen: {self.manager.current if self.manager else 'No manager'}")
        
        # Check if user is logged in
        if not hasattr(app, 'user_id') or not app.user_id:
            # Redirect to login if not logged in
            self.manager.current = 'login'
        else:
            # Connect to ESP device
            self.connect_to_esp_device()
            self.connect_to_esp_device()

    def toggle_slider(self):
        """Toggle slider menu open/closed"""
        if self.slider_open:
            self.close_slider()
        else:
            self.open_slider()
    
    def open_slider(self):
        """Open slider menu"""
        self.ids.slider_menu.slide_in()
        self.slider_open = True
        # Make sure the burger button stays visible and on top
        self.ids.menu_button.opacity = 1.0
        # Force a layout update to ensure button is visible and on top
        Clock.schedule_once(lambda dt: setattr(self.ids.menu_button, 'pos_hint', {'x': 0.02, 'top': 0.98}), 0.1)
    
    def close_slider(self):
        """Close slider menu"""
        self.ids.slider_menu.slide_out()
        self.slider_open = False
    
    def on_accidental_press(self):
        """Handle accidental press button"""
        print("Accidental Press button pressed")
        # Add your implementation here

    def on_permissions(self):
        """Handle permissions button"""
        print("Permissions button pressed")
        
        # Check if permissions screen exists already
        if 'permissions' in self.manager.screen_names:
            # Navigate to existing permissions screen
            self.manager.current = 'permissions'
        else:
            # Import and create the permissions screen
            from screens.permissions.permissions_screen import PermissionsScreen
            permissions_screen = PermissionsScreen(name='permissions')
            self.manager.add_widget(permissions_screen)
            self.manager.current = 'permissions'

    def on_emergency_contacts(self):
        """Handle emergency contacts button"""
        print("Emergency Contacts button pressed")
        # Add your implementation here

    def on_about_us(self):
        """Handle about us button"""
        print("About Us button pressed")
        
        # Check if about_us screen exists already
        if 'about_us' in self.manager.screen_names:
            # Navigate to existing about_us screen
            self.manager.current = 'about_us'
        else:
            # Import and create the about_us screen
            from screens.about_us.about_us_screen import AboutUsScreen
            about_us_screen = AboutUsScreen(name='about_us')
            self.manager.add_widget(about_us_screen)
            self.manager.current = 'about_us'

    def on_update_profile_press(self):
        """Handle update profile button press in the slider menu"""
        print("Update Profile button pressed")
        # Close the slider
        self.close_slider()
        
        # Navigate to profile update screen
        if 'profile_update' in self.manager.screen_names:
            self.manager.current = 'profile_update'
        else:
            # Import and add the profile update screen
            from screens.profile_update.profile_update_screen import ProfileUpdateScreen
            profile_update_screen = ProfileUpdateScreen(name='profile_update')
            self.manager.add_widget(profile_update_screen)
            self.manager.current = 'profile_update'

    def on_info_press(self):
        """Handle info button press"""
        print("Info button pressed")
        # Close the slider
        self.close_slider()
        
        # Navigate to info screen
        if 'info' in self.manager.screen_names:
            self.manager.current = 'info'
        else:
            print("Info screen not found in the screen manager")

    def on_terminate_account_press(self):
        """Handle terminate account button press"""
        print("Terminate account button pressed")
        self.close_slider()
        if 'terminate_account' in self.manager.screen_names:
            self.manager.current = 'terminate_account'

    def on_logout_press(self):
        """Handle logout button press"""
        app = App.get_running_app()
        app.user_identifier = None
        self.manager.current = 'login'

    def show_message(self, title, message):
        """Show a popup message"""
        popup = Popup(
            title=title,
            content=Label(text=message),
            size_hint=(None, None),
            size=(300, 200)
        )
        popup.open()
    
    def show_file_chooser(self):
        """Show file chooser to select an image"""
        print("Showing file chooser")
        view = ModalView(size_hint=(0.9, 0.9))
        file_chooser = FileChooserIconView(filters=['*.png', '*.jpg', '*.jpeg'])
        
        # Add buttons for select and cancel
        buttons_layout = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        select_button = Button(text='Select', size_hint_x=0.5)
        cancel_button = Button(text='Cancel', size_hint_x=0.5)
        
        # Bind events
        select_button.bind(on_release=lambda x: self.on_picture_selected(file_chooser.selection, view))
        cancel_button.bind(on_release=view.dismiss)
        
        # Add widgets to layout
        buttons_layout.add_widget(select_button)
        buttons_layout.add_widget(cancel_button)
        
        layout = BoxLayout(orientation='vertical')
        layout.add_widget(file_chooser)
        layout.add_widget(buttons_layout)
        
        view.add_widget(layout)
        view.open()
    
    def on_picture_selected(self, selection, dialog):
        """Handle selected profile picture"""
        if selection and len(selection) > 0:
            app = App.get_running_app()
            selected_file = selection[0]
            
            try:
                # Get user ID
                user_id = None
                if hasattr(app, 'user_id') and app.user_id:
                    user_id = app.user_id
                else:
                    user_data = app.read_user_data()
                    user_id = user_data.get('user_id')
                
                if user_id:
                    # Cache the profile picture
                    from utils.cache_manager import cache_manager
                    cached_path = cache_manager.cache_profile_picture(user_id, selected_file)
                    
                    # Use cached path if available, otherwise use original
                    if cached_path and os.path.exists(cached_path):
                        selected_file = cached_path
                        print(f"Using cached profile picture: {cached_path}")
            except Exception as e:
                print(f"Error caching profile picture: {str(e)}")
            
            # Update profile picture
            self.ids.slider_menu.profile_picture = selected_file
            
            # Save to app data
            app.update_user_data('profile_picture', selected_file)
            
            # Close dialog
            dialog.dismiss()