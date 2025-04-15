"""
Fallback flag generator for the Safinity app.
This module generates a colored rectangle with a country code when flag images fail to load.
"""
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.app import App

class FallbackFlag(BoxLayout):
    """
    A widget that displays a fallback representation for a country when the flag image fails to load.
    It creates a rectangle with the app's theme color and displays the country code.
    """
    def __init__(self, country_code='', **kwargs):
        super(FallbackFlag, self).__init__(**kwargs)
        self.orientation = 'vertical'
        
        # Use the user's preferred dark green color scheme
        self.bg_color = (0.1, 0.4, 0.1, 1)  # Dark green primary color
        self.text_color = (1, 1, 1, 1)  # White text for contrast
        
        # Create a colored background
        with self.canvas.before:
            Color(*self.bg_color)
            self.rect = Rectangle(pos=self.pos, size=self.size)
        
        # Bind the rectangle size and position to the widget
        self.bind(pos=self._update_rect, size=self._update_rect)
        
        # Add country code label
        self.label = Label(
            text=country_code,
            color=self.text_color,
            font_size='14sp',
            bold=True,
            halign='center',
            valign='middle'
        )
        self.add_widget(self.label)
    
    def _update_rect(self, *args):
        """Update the rectangle position and size when the widget changes"""
        self.rect.pos = self.pos
        self.rect.size = self.size
    
    def set_country_code(self, code):
        """Set the country code to display"""
        self.label.text = code

def create_fallback_flag(country_code, width=50, height=30):
    """
    Create and return a fallback flag widget with the given country code.
    
    Args:
        country_code (str): The 2-letter country code to display
        width (int): Width of the flag in dp
        height (int): Height of the flag in dp
        
    Returns:
        FallbackFlag: A widget configured to display a fallback flag
    """
    flag = FallbackFlag(country_code=country_code)
    flag.size_hint = (None, None)
    flag.size = (width, height)
    return flag
