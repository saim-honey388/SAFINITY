from kivy.uix.screenmanager import Screen
from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.app import App

class AboutUsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def on_enter(self):
        """Called when the screen is entered"""
        print("AboutUsScreen entered")
    
    def on_back_press(self):
        """Handle back button press"""
        print("Back button pressed")
        self.manager.current = 'home'

# Load the kv file
Builder.load_file('screens/about_us/about_us_screen.kv')