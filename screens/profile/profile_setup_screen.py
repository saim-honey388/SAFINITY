from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.app import App
from kivy.lang import Builder
from utils.database_service import DatabaseService
import traceback

# Load the KV file
Builder.load_file('screens/profile/profile_setup_screen.kv')

class ProfileSetupScreen(Screen):
    first_name = ObjectProperty(None)
    last_name = ObjectProperty(None)
    dob_input = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db = DatabaseService()
        self.phone_number = None
        print("[DEBUG] ProfileSetupScreen initialized")

    def on_enter(self):
        """Called when entering the profile setup screen"""
        print("[DEBUG] ProfileSetupScreen entered")
        try:
            app = App.get_running_app()
            if hasattr(app, 'phone_number'):
                self.phone_number = app.phone_number
                print(f"[DEBUG] Phone number loaded: {self.phone_number}")
            else:
                print("[DEBUG] No phone number found in app data")
        except Exception as e:
            print(f"[DEBUG] Error in ProfileSetupScreen on_enter: {str(e)}")

    def show_message(self, title, message):
        popup = Popup(
            title=title,
            content=Label(text=message, text_size=(280, None), halign='center'),
            size_hint=(None, None),
            size=(300, 200)
        )
        popup.open()

    def update_dob(self):
        """Update the DOB input field based on spinner selections"""
        day = self.ids.day_spinner.text if self.ids.day_spinner.text != 'Day' else ''
        month = self.ids.month_spinner.text if self.ids.month_spinner.text != 'Month' else ''
        year = self.ids.year_spinner.text if self.ids.year_spinner.text != 'Year' else ''

        if day and month and year:
            self.ids.dob_input.text = f"{day}/{month}/{year}"
            print(f"[DEBUG] DOB updated: {self.ids.dob_input.text}")
        else:
            self.ids.dob_input.text = ''

    def validate_input(self):
        """Validate all input fields"""
        try:
            first_name = self.ids.first_name_input.text.strip()
            last_name = self.ids.last_name_input.text.strip()
            dob = self.ids.dob_input.text.strip()
            use_case = self.ids.use_case_spinner.text

            print(f"[DEBUG] Validating - First Name: {first_name}")
            print(f"[DEBUG] Validating - Last Name: {last_name}")
            print(f"[DEBUG] Validating - DOB: {dob}")
            print(f"[DEBUG] Validating - Use Case: {use_case}")

            if not first_name or not last_name:
                self.show_message('Error', 'Please enter your full name')
                return False

            if not dob or dob == 'DD/MM/YYYY':
                self.show_message('Error', 'Please select your date of birth')
                return False

            if not any([self.ids.male_checkbox.active, 
                       self.ids.female_checkbox.active, 
                       self.ids.other_checkbox.active]):
                self.show_message('Error', 'Please select your gender')
                return False

            if use_case == 'Primary Use Case':
                self.show_message('Error', 'Please select your primary use case')
                return False

            return True
        except Exception as e:
            print(f"[DEBUG] Validation error: {e}")
            self.show_message('Error', 'An error occurred while validating input')
            return False

    def get_selected_gender(self):
        """Get the selected gender from checkboxes"""
        if self.ids.male_checkbox.active:
            return 'Male'
        elif self.ids.female_checkbox.active:
            return 'Female'
        elif self.ids.other_checkbox.active:
            return 'Other'
        return None

    def save_profile(self, full_name, date_of_birth, gender, address, profile_picture):
        """Save user profile information"""
        try:
            # Validate inputs
            if not full_name or not date_of_birth or not gender:
                self.show_error("Please fill in all required fields")
                return

            # Get user data from app instance
            app = App.get_running_app()
            if not hasattr(app, 'verified_phone_number'):
                print("Error: No verified phone number found")
                self.show_error("Verification data not found")
                return

            print(f"\n=== Profile Setup Debug ===")
            print(f"Verified phone number: {app.verified_phone_number}")
            
            # Get user from database using phone number
            user = self.db.get_user_by_credentials(app.verified_phone_number, None)
            if not user:
                print("Error: User not found")
                self.show_error("User data not found")
                return

            print(f"Found user with phone number: {app.verified_phone_number}")
            print(f"Current user data: {user}")

            # Create profile data dictionary with only the fields we want to update
            profile_data = {
                'full_name': full_name,
                'date_of_birth': date_of_birth,
                'gender': gender,
                'address': address if address else '',
                'profile_picture': profile_picture if profile_picture else ''
            }
            
            print(f"Profile data to update: {profile_data}")

            # Use update_user_profile method to update and display database contents
            success, message = self.db.update_user_profile(app.verified_phone_number, profile_data)
            
            if success:
                print("Profile saved successfully")
                # Store user ID in app instance for later use
                app.user_id = str(user['id'])  # Use the original user ID
                # Proceed to home screen
                self.manager.current = 'home'
            else:
                print(f"Failed to save profile: {message}")
                self.show_error(message or "Failed to save profile information")

        except Exception as e:
            print(f"Error in save_profile: {str(e)}")
            traceback.print_exc()
            self.show_error("An error occurred while saving profile")

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

    def submit_form(self):
        """Handle form submission"""
        try:
            # Validate inputs first
            if not self.validate_input():
                return

            # Get form data
            first_name = self.ids.first_name_input.text.strip()
            last_name = self.ids.last_name_input.text.strip()
            full_name = f"{first_name} {last_name}"
            date_of_birth = self.ids.dob_input.text.strip()
            gender = self.get_selected_gender()
            address = self.ids.address_input.text.strip() if hasattr(self.ids, 'address_input') else ""
            profile_picture = ""  # Will be handled later when we implement image upload

            # Save profile
            self.save_profile(full_name, date_of_birth, gender, address, profile_picture)

        except Exception as e:
            print(f"Error in submit_form: {str(e)}")
            traceback.print_exc()
            self.show_error("An error occurred while submitting the form")