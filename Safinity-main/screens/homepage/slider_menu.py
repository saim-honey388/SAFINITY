from kivy.uix.boxlayout import BoxLayout
from kivy.animation import Animation
from kivy.properties import ObjectProperty, StringProperty, BooleanProperty
from kivy.app import App
from kivy.clock import Clock
from utils.cache_manager import cache_manager
from kivy.cache import Cache
import os

class SliderMenu(BoxLayout):
    profile_picture = StringProperty('assets/default_profile.png')
    user_name = StringProperty('User Name')
    is_open = BooleanProperty(False)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Initialize size and position
        self.size_hint_x = 0.1  # 80% of screen width
        self.pos_hint = {'x': -0.1, 'top': 1}  # Right aligned
        self.opacity = 0  # Start hidden
        
        # Try to load user data if available
        app = App.get_running_app()
        if hasattr(app, 'user_data') and app.user_data:
            self.user_name = app.user_data.get('full_name', 'User')
            if app.user_data.get('profile_picture'):
                self.profile_picture = app.user_data.get('profile_picture')
                
        # Schedule a function to ensure proper initialization after kv loading
        Clock.schedule_once(self._post_init, 0.1)
    
    def _post_init(self, dt):
        """Ensure proper initial state"""
        self.x = self.parent.width  # Start off-screen on the right
        self.opacity = 1  # Make visible but off-screen
    
    def slide_in(self):
        """Slide the menu in from the right"""
        if not self.is_open:
            # Calculate target position (right side of screen)
            target_x = self.parent.width - self.width
            
            # Create and start animation
            anim = Animation(x=target_x, duration=0.3)
            anim.start(self)
            self.is_open = True

    def slide_out(self):
        """Slide the menu out to the right"""
        if self.is_open:
            # Move back off-screen
            anim = Animation(x=self.parent.width, duration=0.3)
            anim.start(self)
            self.is_open = False
        
    def update_profile_picture(self):
        """Handle profile picture update button press"""
        print("Update profile picture requested")
        # Navigate to profile update screen if it exists
        app = App.get_running_app()
        if app.root and hasattr(app.root, 'current'):
            if 'profile_update' in app.root.screen_names:
                app.root.current = 'profile_update'
            else:
                print("Profile update screen not found")