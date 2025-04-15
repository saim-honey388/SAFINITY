from kivy.uix.screenmanager import Screen
from kivy.properties import ListProperty, ObjectProperty
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import json
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import AsyncImage
from kivy.uix.spinner import Spinner, SpinnerOption
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.dropdown import DropDown
from kivy.uix.button import Button
import traceback
import os
import requests
import shutil
from pathlib import Path

# Create the SQLAlchemy base class using the new recommended approach
Base = declarative_base()

# Define the UserCountry model
class UserCountry(Base):
    __tablename__ = 'user_country'
    
    id = Column(Integer, primary_key=True)
    country_name = Column(String)
    dial_code = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

class ScrollableSpinner(Spinner):
    def __init__(self, **kwargs):
        self.dropdown = None
        super().__init__(**kwargs)
        
    def _on_dropdown_select(self, text):
        self.text = text
        if self.dropdown:
            self.dropdown.dismiss()
            
    def _update_dropdown(self, *largs):
        """Update the dropdown list with all countries"""
        try:
            if not self.dropdown:
                self.dropdown = DropDown()
            
            self.dropdown.clear_widgets()
            self.dropdown.size_hint_y = None
            self.dropdown.size_hint_x = None
            self.dropdown.width = dp(400)
            
            # Create container for options with smaller height
            container = BoxLayout(
                orientation='vertical',
                size_hint_y=None,
                height=dp(150)  # Reduced from 200 to 150
            )
            
            # Create ScrollView
            scroll = ScrollView(
                size_hint=(1, 1),
                do_scroll_x=False,
                do_scroll_y=True,
                bar_width=dp(10),
                scroll_type=['bars', 'content'],
                bar_color=[0.7, 0.7, 0.7, 0.9],
                bar_inactive_color=[0.7, 0.7, 0.7, 0.2],
                scroll_wheel_distance=dp(40)  # Reduced scroll distance
            )
            
            # Create grid for options
            grid = GridLayout(
                cols=1,
                spacing=dp(1),  # Reduced spacing
                size_hint_y=None,
                padding=[dp(5), dp(5), dp(15), dp(5)]
            )
            grid.bind(minimum_height=grid.setter('height'))
            
            # Get app instance and screen
            app = App.get_running_app()
            if not app or not app.root:
                print("Error: App or root not available")
                return
                
            screen = app.root.get_screen('flags_screen')
            if not screen:
                print("Error: Screen not found")
                return
                
            print(f"Total values to display: {len(self.values)}")
            
            # Add all countries to the grid with reduced height
            for country_name in self.values:
                try:
                    # Find country data
                    country_data = next((c for c in screen.countries if c['name'] == country_name), None)
                    if not country_data:
                        continue
                    
                    # Main option container with reduced height
                    option = BoxLayout(
                        orientation='horizontal',
                        size_hint_y=None,
                        height=dp(40),  # Reduced height for each option
                        spacing=dp(10),
                        padding=[dp(5), 0]
                    )
                    
                    # Left container for flag (fixed width)
                    flag_section = BoxLayout(
                        orientation='horizontal',
                        size_hint_x=None,
                        width=dp(60),
                        padding=[dp(5), 0]
                    )
                    
                    # Flag image with reduced size
                    flag = AsyncImage(
                        source=country_data.get('image', ''),
                        size_hint=(None, None),
                        size=(dp(30), dp(20)),  # Reduced flag size
                        pos_hint={'center_x': 0.5, 'center_y': 0.5}
                    )
                    flag_section.add_widget(flag)
                    
                    # Right container for text
                    text_section = BoxLayout(
                        orientation='horizontal',
                        size_hint_x=1,
                        padding=[0, 0, dp(5), 0]
                    )
                    
                    # Button with country name
                    btn = Button(
                        text=country_name,
                        size_hint=(1, None),
                        height=dp(40),  # Reduced button height
                        background_normal='',
                        background_color=(1, 1, 1, 1),
                        color=(0, 0, 0, 1),
                        halign='left',
                        valign='middle',
                        font_size='14sp'  # Reduced font size
                    )
                    
                    # Set the button's text size and position
                    def update_text_size(instance, size):
                        instance.text_size = (size[0] - dp(10), size[1])
                        instance.padding = [dp(10), 0]
                        
                    btn.bind(size=update_text_size)
                    btn.bind(on_release=lambda btn, name=country_name: self._on_dropdown_select(name))
                    
                    # Add widgets to their containers
                    text_section.add_widget(btn)
                    option.add_widget(flag_section)
                    option.add_widget(text_section)
                    
                    # Add the complete option to the grid
                    grid.add_widget(option)
                    
                except Exception as e:
                    print(f"Error adding country {country_name}: {str(e)}")
                    continue
            
            # Update grid height
            grid.height = len(self.values) * dp(40)  # Adjust for reduced option height
            
            # Add widgets to container
            scroll.add_widget(grid)
            container.add_widget(scroll)
            self.dropdown.add_widget(container)
            
            print(f"Added {len(grid.children)} countries to dropdown")
            
        except Exception as e:
            print(f"Error creating dropdown items: {str(e)}")
            traceback.print_exc()

    def on_release(self, *args):
        """Handle spinner release to show dropdown"""
        try:
            self._update_dropdown()
            
            if not self.dropdown.parent:
                self.dropdown.open(self)
            
            # Get spinner position in window
            spinner_x = self.to_window(*self.pos)[0]
            spinner_y = self.to_window(*self.pos)[1]
            
            # Position dropdown above the spinner with adjusted height
            x = spinner_x
            y = spinner_y + self.height + dp(10)  # Added small padding
            
            # Get window height
            window_height = Window.height
            
            # Calculate maximum available height
            max_height = window_height - y - dp(50)  # Leave some padding
            
            # Adjust dropdown height if needed
            if max_height < dp(150):  # Reduced from 200 to 150
                y = spinner_y - dp(150)  # Show below instead
            
            # Set final position
            self.dropdown.pos = (x, y)
            
        except Exception as e:
            print(f"Error showing dropdown: {e}")
            traceback.print_exc()

class FlagsScreen(Screen):
    countries = ListProperty([])
    country_spinner = ObjectProperty(None)
    selected_flag = ObjectProperty(None)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.selected_country = None
        self.flags_cache_dir = os.path.join(os.path.dirname(__file__), 'flags_cache')
        os.makedirs(self.flags_cache_dir, exist_ok=True)
        self._init_db()
        Clock.schedule_once(self._init_ui)
        print("FlagsScreen initialized")

    def _init_ui(self, dt):
        """Initialize the UI after the kv file is loaded"""
        try:
            self.load_countries()  # Load countries first
            print("Initializing UI with", len(self.countries), "countries")
            
            if not self.countries:
                print("No countries data available during UI initialization")
                return
                
            if hasattr(self.ids, 'country_spinner'):
                self.country_spinner = self.ids.country_spinner
                self.country_spinner.text = 'Select country'
                country_names = [country['name'] for country in self.countries]
                self.country_spinner.values = country_names
                print(f"Added {len(country_names)} countries to spinner")
            else:
                print("Warning: country_spinner not found in ids")
            
        except Exception as e:
            print(f"Error initializing UI: {e}")
            traceback.print_exc()

    def _init_db(self):
        """Initialize database connection and create tables"""
        try:
            # Get the absolute path to the project directory
            project_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            db_file = os.path.join(project_dir, 'safinity.db')

            # Create SQLite URL with absolute path
            db_url = f'sqlite:///{db_file}'

            # Create engine
            self.engine = create_engine(db_url, echo=True)
            Base.metadata.create_all(self.engine)
            self.Session = sessionmaker(bind=self.engine)
            print("Database initialized successfully")
        except Exception as e:
            print(f"Error initializing database: {e}")
            traceback.print_exc()

    def load_countries(self):
        """Load countries from JSON file"""
        try:
            json_path = os.path.join(os.path.dirname(__file__), '..', '..', 'countries.json')
            print(f"Attempting to load countries from: {json_path}")
            
            if not os.path.exists(json_path):
                print(f"Error: countries.json not found at {json_path}")
                print("Current working directory:", os.getcwd())
                return
            
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict) and 'countries' in data:
                    self.countries = data['countries']
                else:
                    self.countries = data
                
            print(f"Loaded {len(self.countries)} countries from JSON file")
            if len(self.countries) > 0:
                print("First few countries:", [c.get('name') for c in self.countries[:5]])
            else:
                print("Warning: No countries loaded from JSON file")
                
        except Exception as e:
            print(f"Error loading countries: {str(e)}")
            traceback.print_exc()
            self.countries = []

    def store_country_in_db(self, country_data):
        """Store selected country in database using SQLAlchemy"""
        session = None
        try:
            session = self.Session()
            
            # Create new UserCountry instance
            user_country = UserCountry(
                country_name=country_data['name'],
                dial_code=country_data['dial_code'].replace('+', '')  # Store without + symbol
            )
            
            # Add and commit to database
            session.add(user_country)
            session.commit()
            print(f"Stored country in database: {country_data['name']}")
            
        except Exception as e:
            print(f"Error storing country in database: {e}")
            traceback.print_exc()
            if session:
                session.rollback()
        finally:
            if session:
                session.close()

    def get_cached_flag_path(self, country_code):
        return os.path.join(self.flags_cache_dir, f"{country_code.lower()}.png")

    def download_flag(self, country_code, image_url):
        cached_path = self.get_cached_flag_path(country_code)
        if os.path.exists(cached_path):
            return cached_path
            
        try:
            response = requests.get(image_url, stream=True, timeout=5)
            if response.status_code == 200:
                with open(cached_path, 'wb') as f:
                    response.raw.decode_content = True
                    shutil.copyfileobj(response.raw, f)
                return cached_path
        except Exception as e:
            print(f"Error downloading flag for {country_code}: {str(e)}")
        return None

    def on_country_selected(self, country_name):
        try:
            country = next((c for c in self.countries if c['name'] == country_name), None)
            if not country:
                return

            app = App.get_running_app()
            app.country_code = country['dial_code'].replace('+', '')
            app.selected_country = country

            # Try to load cached flag first
            cached_flag = self.get_cached_flag_path(country['code'])
            if os.path.exists(cached_flag):
                self.selected_flag.source = cached_flag
                return

            # If not cached, try to download
            image_url = country['image']
            downloaded_flag = self.download_flag(country['code'], image_url)
            if downloaded_flag:
                self.selected_flag.source = downloaded_flag

            
            else:
                 # Use fallback image if download fails
                fallback_path = os.path.join(os.path.dirname(__file__), 'fallback_flag.png')
                self.selected_flag.source = fallback_path if os.path.exists(fallback_path) else ''
                

        except Exception as e:
            print(f"Error selecting country: {str(e)}")
            self.selected_flag.source = ''

    def on_continue(self):
        """Handle continue button press"""
        try:
            if not self.selected_country:
                self.show_message("Please select a country")
                return

            # Store country in database using SQLAlchemy
            self.store_country_in_db(self.selected_country)

            # Navigate to phone screen
            if 'phone' not in self.manager.screen_names:
                from screens.phone.phone_number_screen import PhoneNumberScreen
                self.manager.add_widget(PhoneNumberScreen(name='phone'))
            self.manager.current = 'phone'
            
        except Exception as e:
            print(f"Error in on_continue: {e}")
            self.show_message("Error proceeding to next screen")


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

    def on_enter(self):
        """Called when screen is entered"""
        try:
            if hasattr(self.ids, 'country_spinner'):
                self.ids.country_spinner.text = 'Select country'
            self.selected_country = None
        except Exception as e:
            print(f"Error in on_enter: {e}")
            traceback.print_exc()