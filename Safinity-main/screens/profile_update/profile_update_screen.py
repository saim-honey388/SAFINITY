from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty, BooleanProperty, StringProperty
from kivy.uix.label import Label
from kivy.app import App
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.metrics import dp
from utils.database_service import DatabaseService
from utils.veevotech_service import VeevotechService
from utils.phone_util import normalize_phone_number, find_phone_number_variants
import traceback
import os

# Load the KV file
Builder.load_file('screens/profile_update/profile_update_screen.kv')

class ProfileUpdateScreen(Screen):
    edit_mode = BooleanProperty(False)  # Control whether fields are editable
    phone_changed = BooleanProperty(False)  # Track if phone number has changed
    original_phone = StringProperty("")  # Store original phone number
    updated_phone = StringProperty('')  # Store updated phone number
    otp_verified = BooleanProperty(False)  # Track if OTP is verified
    resend_timer_active = BooleanProperty(False)  # OTP timer active
    countdown = StringProperty('60')  # OTP countdown timer

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db = DatabaseService()
        self.veevotech = VeevotechService()
        self.countdown_event = None
        print("[DEBUG] ProfileUpdateScreen initialized")
        
    def on_enter(self):
        """Called when the screen is entered"""
        try:
            print("[DEBUG] Profile update screen entered")
            
            # Reset flags to their default state
            self.edit_mode = False
            self.phone_changed = False
            self.otp_verified = False
            self.original_phone = ""  # Use empty string instead of None
            
            # Update UI for non-edit mode
            self.ids.edit_button.text = "Edit Profile"
            
            # Hide OTP section
            if hasattr(self.ids, 'otp_section'):
                self.ids.otp_section.opacity = 0
                self.ids.otp_section.height = 0
            
            # Load user data
            self.load_user_data()
            
            # Important: Add a slight delay before updating field states
            # This ensures the screen is fully rendered first
            Clock.schedule_once(lambda dt: self._reset_after_enter(), 0.2)
            
        except Exception as e:
            print(f"[DEBUG] Error in on_enter: {str(e)}")
            traceback.print_exc()
    
    def _reset_after_enter(self):
        """Reset all fields after screen enter with delay"""
        try:
            print("[DEBUG] Resetting fields after entering screen")
            
            # Update all field states
            self._update_field_states()
            
            # Extra handling for phone field
            if hasattr(self.ids, 'phone_input'):
                self.ids.phone_input.disabled = True
                self.ids.phone_input.hint_text = "Enter your phone number"
                print(f"[DEBUG] Reset phone input: disabled={self.ids.phone_input.disabled}")
            
        except Exception as e:
            print(f"[DEBUG] Error in _reset_after_enter: {str(e)}")
            traceback.print_exc()
    
    def toggle_edit_mode(self):
        """Toggle edit mode to enable/disable input fields"""
        try:
            # Toggle edit mode
            self.edit_mode = not self.edit_mode
            print(f"[DEBUG] Edit mode toggled to: {self.edit_mode}")
            
            # Update button text
            self.ids.edit_button.text = "Cancel Edit" if self.edit_mode else "Edit Profile"
            
            # Use a delay to update phone input properties
            # This helps avoid race conditions in Kivy's property system
            if self.edit_mode:
                # Schedule phone field update for next frame
                Clock.schedule_once(self.enable_phone_field, 0.1)
                
                # Reset verification state immediately
                self.original_phone = self.ids.phone_input.text.strip() or ""
                self.phone_changed = False
                self.otp_verified = False
                
                # Hide OTP section
                self.ids.otp_section.opacity = 0
                self.ids.otp_section.height = 0
                
                # Update other fields
                self._update_field_states()
            else:
                # If canceling, reload original data
                self.load_user_data()
                
                # Update all field states
                self._update_field_states()
                
        except Exception as e:
            print(f"[DEBUG] Error in toggle_edit_mode: {str(e)}")
            traceback.print_exc()
    
    def load_user_data(self):
        """Load user data from database and populate fields"""
        try:
            app = App.get_running_app()
            user_id = None
            
            # Try to get user_id from app property
            if hasattr(app, 'user_id') and app.user_id:
                user_id = app.user_id
                print(f"[DEBUG] Using user ID from app property: {user_id}")
            else:
                # Fallback to user_data
                user_data = app.read_user_data()
                user_id = user_data.get('user_id')
                print(f"[DEBUG] Using user ID from user_data: {user_id}")
            
            if not user_id:
                self.show_error("No user ID found. Please log in again.")
                return
            
            # Get user info from database
            user = self.db.get_user_info(user_id)
            if not user:
                self.show_error("User information not found. Please log in again.")
                return
            
            print(f"[DEBUG] User data loaded: {user}")
            
            # Populate fields with user data
            if user.get('full_name'):
                # Split full name into first and last name
                name_parts = user.get('full_name', '').split(' ', 1)
                if len(name_parts) >= 1:
                    self.ids.first_name_input.text = name_parts[0]
                if len(name_parts) >= 2:
                    self.ids.last_name_input.text = name_parts[1]
            
            # Set email
            if user.get('email'):
                self.ids.email_input.text = user.get('email')
            
            # Set phone
            if user.get('phone_number'):
                self.ids.phone_input.text = user.get('phone_number')
                self.original_phone = user.get('phone_number')
                
                # Ensure phone_input is properly enabled/disabled based on edit_mode
                self.ids.phone_input.disabled = not self.edit_mode
            
            # Set DOB
            if user.get('date_of_birth'):
                self.ids.dob_input.text = user.get('date_of_birth')
                # Try to parse DOB to set spinners
                try:
                    dob_parts = user.get('date_of_birth').split('/')
                    if len(dob_parts) == 3:
                        day, month, year = dob_parts
                        # Convert month to name
                        month_names = ['January', 'February', 'March', 'April', 'May', 'June', 
                                      'July', 'August', 'September', 'October', 'November', 'December']
                        try:
                            month_idx = int(month)
                            if 1 <= month_idx <= 12:
                                month_name = month_names[month_idx - 1]
                                self.ids.day_spinner.text = day
                                self.ids.month_spinner.text = month_name
                                self.ids.year_spinner.text = year
                        except ValueError:
                            pass
                except Exception as e:
                    print(f"[DEBUG] Error parsing DOB: {e}")
            
            # Set gender
            if user.get('gender'):
                gender = user.get('gender')
                if gender == 'Male':
                    self.ids.male_checkbox.active = True
                elif gender == 'Female':
                    self.ids.female_checkbox.active = True
                elif gender == 'Other':
                    self.ids.other_checkbox.active = True
            
            # Set use case
            if user.get('use_case'):
                self.ids.use_case_spinner.text = user.get('use_case')
            
            # Set address
            if user.get('address'):
                self.ids.address_input.text = user.get('address')
            
        except Exception as e:
            print(f"[DEBUG] Error loading user data: {str(e)}")
            traceback.print_exc()
            self.show_error("An error occurred while loading your profile data")
    
    def update_dob(self):
        """Update the DOB input field based on spinner selections"""
        day = self.ids.day_spinner.text if self.ids.day_spinner.text != 'Day' else ''
        month = self.ids.month_spinner.text if self.ids.month_spinner.text != 'Month' else ''
        year = self.ids.year_spinner.text if self.ids.year_spinner.text != 'Year' else ''
        
        # Convert month name to number
        month_names = ['January', 'February', 'March', 'April', 'May', 'June', 
                      'July', 'August', 'September', 'October', 'November', 'December']
        if month in month_names:
            month_num = str(month_names.index(month) + 1)
            # Pad with leading zero if needed
            if len(month_num) == 1:
                month_num = f"0{month_num}"
            month = month_num
        
        if day and month and year:
            # Ensure day is two digits
            if len(day) == 1:
                day = f"0{day}"
            self.ids.dob_input.text = f"{day}/{month}/{year}"
            print(f"[DEBUG] DOB updated: {self.ids.dob_input.text}")
        else:
            self.ids.dob_input.text = ''
    
    def get_selected_gender(self):
        """Get the selected gender from checkboxes"""
        if self.ids.male_checkbox.active:
            return 'Male'
        elif self.ids.female_checkbox.active:
            return 'Female'
        elif self.ids.other_checkbox.active:
            return 'Other'
        return None
    
    def validate_input(self):
        """Validate all input fields"""
        try:
            # For profile update, we don't need to enforce all fields being filled
            # Just validate that email and phone formats are correct if provided
            
            email = self.ids.email_input.text.strip()
            phone = self.ids.phone_input.text.strip()
            
            # Basic email format validation
            if email and '@' not in email:
                self.show_error('Please enter a valid email address')
                return False
            
            # Phone validation using the new phone_util module
            if phone:
                try:
                    # Try to normalize the phone number
                    normalized = normalize_phone_number(phone)
                    
                    # Basic validation - check if we got something meaningful
                    if not normalized or len(normalized.replace('+', '').strip()) < 6:
                        self.show_error('Please enter a valid phone number')
                        return False
                    
                    # Print normalized result for debugging
                    print(f"[DEBUG] Phone validated and normalized: {phone} → {normalized}")
                    
                except Exception as e:
                    print(f"[DEBUG] Phone validation error: {str(e)}")
                    self.show_error('Please enter a valid phone number')
                    return False
            
            return True
            
        except Exception as e:
            print(f"[DEBUG] Validation error: {e}")
            self.show_error('An error occurred while validating input')
            return False
    
    def save_profile(self):
        """Save updated profile information"""
        try:
            # Validate inputs
            if not self.validate_input():
                return
            
            # Check if phone number is changed and verified
            if self.phone_changed and not self.otp_verified:
                self.show_error("Please verify your new phone number before saving")
                return
            
            # Get app instance and user ID
            app = App.get_running_app()
            user_id = None
            
            if hasattr(app, 'user_id') and app.user_id:
                user_id = app.user_id
            else:
                user_data = app.read_user_data()
                user_id = user_data.get('user_id')
            
            if not user_id:
                self.show_error("No user ID found. Please log in again.")
                return
            
            # Get current user info to check for email/phone changes
            current_user = self.db.get_user_info(user_id)
            if not current_user:
                self.show_error("User data not found.")
                return
            
            # Get form data
            first_name = self.ids.first_name_input.text.strip()
            last_name = self.ids.last_name_input.text.strip()
            full_name = f"{first_name} {last_name}" if first_name or last_name else ""
            
            email = self.ids.email_input.text.strip()
            
            # Use phone_util to normalize phone number
            phone = self.ids.phone_input.text.strip()
            if phone:
                original_phone = phone
                phone = normalize_phone_number(phone)
                if original_phone != phone and phone != self.original_phone:
                    print(f"[DEBUG] Normalized phone number: {original_phone} → {phone}")
            
            # Use normalized phone if verified, or original phone if not changed
            phone = phone if self.otp_verified or not self.phone_changed else self.original_phone
            
            date_of_birth = self.ids.dob_input.text.strip()
            gender = self.get_selected_gender()
            use_case = self.ids.use_case_spinner.text
            if use_case == 'Primary Use Case':
                use_case = ''
            
            address = self.ids.address_input.text.strip()
            
            # Check if email has changed and verify uniqueness
            if email and email != current_user.get('email'):
                # Check if email is unique
                if self.db.check_credential_exists('email', email, user_id):
                    self.show_error(f"Email {email} is already in use by another account. Please use a different email.")
                    # Restore previous email
                    self.ids.email_input.text = current_user.get('email', '')
                    return
            
            # Create profile data dictionary
            profile_data = {
                'full_name': full_name,
                'email': email,
                'phone_number': phone,
                'date_of_birth': date_of_birth,
                'gender': gender,
                'use_case': use_case,
                'address': address
            }
            
            # Update user profile
            success, message = self.db.update_user_profile(user_id, profile_data)
            
            if success:
                print("[DEBUG] Profile updated successfully")
                self.show_message('Success', 'Profile updated successfully')
                # Disable edit mode
                self.edit_mode = False
                self.ids.edit_button.text = "Edit Profile"
                # Reset phone verification state
                self.phone_changed = False
                self.otp_verified = False
                self.original_phone = ""  # Clear this to force refresh
                
                # Schedule a delayed reset of field states 
                # to ensure proper rendering when we return to this screen
                Clock.schedule_once(lambda dt: self._update_field_states(), 0.1)
                
                # Go back to home screen with delay to ensure states are saved
                Clock.schedule_once(lambda dt: self.go_back(), 0.2)
            else:
                self.show_error(message or "Failed to update profile")
            
        except Exception as e:
            print(f"[DEBUG] Error updating profile: {str(e)}")
            traceback.print_exc()
            self.show_error("An error occurred while saving your profile")
    
    def show_message(self, title, message):
        """Show message popup"""
        from kivy.uix.popup import Popup
        from kivy.uix.label import Label
        
        popup = Popup(
            title=title,
            content=Label(text=message, text_size=(280, None), halign='center'),
            size_hint=(None, None),
            size=(300, 200)
        )
        popup.open()
    
    def show_error(self, message):
        """Show a simple error toast that disappears on click"""
        from kivy.uix.label import Label
        from kivy.animation import Animation
        from kivy.metrics import dp
        from kivy.graphics import Color, Rectangle
        
        # Create a simple label with red background
        error_label = Label(
            text=message,
            color=(1, 1, 1, 1),  # White text
            font_size=dp(16),
            size_hint=(None, None),
            size=(dp(300), dp(100)),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            halign='center',
            valign='middle'
        )
        
        # Enable text wrapping
        error_label.text_size = (dp(280), None)
        error_label.bind(texture_size=error_label.setter('texture_size'))
        
        # Add red background
        with error_label.canvas.before:
            Color(1, 0.3, 0.3, 1)  # Red background
            rect = Rectangle(pos=error_label.pos, size=error_label.size)
        
        # Update rectangle when label position/size changes
        def update_rect(instance, value):
            rect.pos = instance.pos
            rect.size = instance.size
        error_label.bind(pos=update_rect, size=update_rect)
        
        # Add to screen
        self.add_widget(error_label)
        
        # Make it disappear when clicked
        def on_touch(instance, touch):
            if error_label.collide_point(*touch.pos):
                self.remove_widget(error_label)
                return True
            
        error_label.bind(on_touch_down=on_touch)
        
        # Auto-remove after 5 seconds
        def remove_label(dt):
            if error_label in self.children:
                self.remove_widget(error_label)
                
        Clock.schedule_once(remove_label, 4)
    
    def go_back(self):
        """Go back to home screen"""
        self.manager.current = 'home'
    
    def on_phone_input_change(self, instance, value):
        """Called when phone number input changes"""
        if not self.edit_mode:
            return
            
        # Normalize phone for comparison
        normalized_value = normalize_phone_number(value.strip())
        normalized_original = normalize_phone_number(self.original_phone)
        
        # Check if phone number has changed
        if normalized_value != normalized_original:
            # Check if user is allowed to change phone number (24-hour restriction)
            app = App.get_running_app()
            user_id = getattr(app, 'user_id', "") or app.read_user_data().get('user_id', "")
            
            if not user_id:
                self.show_error("No user ID found. Please log in again.")
                # Revert phone change
                self.ids.phone_input.text = self.original_phone
                return
                
            # Check if enough time has passed since last phone change
            allowed, details = self.db.check_phone_change_allowed(user_id)
            
            if not allowed:
                # Not enough time has passed, show error message
                hours_remaining = details.get('hours_remaining', 24)
                error_msg = f"You can only change your phone number once every 24 hours. Please wait {hours_remaining} more hours."
                self.show_error(error_msg)
                
                # Revert phone change
                self.ids.phone_input.text = self.original_phone
                return
                
            # Allow phone change
            self.phone_changed = True
            self.updated_phone = normalized_value
            self.otp_verified = False
            # Show OTP section
            self.ids.otp_section.opacity = 1
            self.ids.otp_section.height = dp(60)
            self.ids.otp_input.disabled = False
            self.ids.verify_otp_button.disabled = False
        else:
            self.phone_changed = False
            self.ids.otp_section.opacity = 0
            self.ids.otp_section.height = 0
            self.otp_verified = True  # Original phone is already verified
    
    def send_otp(self):
        """Send OTP to the new phone number"""
        if not self.phone_changed or not self.updated_phone:
            return
            
        try:
            response = self.veevotech.send_verification_code(self.updated_phone)
            if response['status'] == 'pending':
                self.show_message('OTP Sent', 'A verification code has been sent to your phone')
                self.start_countdown()
            else:
                self.show_error(response.get('message', 'Failed to send verification code'))
        except Exception as e:
            print(f"[DEBUG] Error sending OTP: {str(e)}")
            traceback.print_exc()
            self.show_error("Failed to send verification code")
    
    def verify_otp(self):
        """Verify the entered OTP"""
        if not self.phone_changed:
            return
            
        otp = self.ids.otp_input.text.strip()
        if not otp:
            self.show_error("Please enter the verification code")
            return
            
        try:
            # Verify OTP using VeevotechService
            result = self.veevotech.verify_code(self.updated_phone, otp)
            if result['status'] == 'approved':
                self.otp_verified = True
                self.show_message('Success', 'Phone number verified successfully')
                
                # Hide OTP section after successful verification
                self.ids.otp_section.opacity = 0
                self.ids.otp_section.height = 0
                
                # Update status to indicate success without changing properties that might
                # interfere with input field accessibility
                self.ids.phone_input.hint_text = "Phone number verified"
            else:
                self.otp_verified = False
                self.show_error(result.get('message', 'Invalid verification code'))
                
                # Revert to original phone number and hide OTP section
                self.ids.phone_input.text = self.original_phone
                self.ids.otp_section.opacity = 0
                self.ids.otp_section.height = 0
                self.phone_changed = False
                
            # Ensure phone input is properly enabled in edit mode
            if self.edit_mode:
                self.ids.phone_input.disabled = False
                print("[DEBUG] Phone input field enabled after verification")
                
        except Exception as e:
            print(f"[DEBUG] Error verifying OTP: {str(e)}")
            traceback.print_exc()
            self.show_error("Failed to verify the code")
            
            # Revert to original phone number on error
            self.ids.phone_input.text = self.original_phone
            self.ids.otp_section.opacity = 0
            self.ids.otp_section.height = 0
            self.phone_changed = False
            
            # Ensure phone input remains enabled in edit mode
            if self.edit_mode:
                self.ids.phone_input.disabled = False
                
    def start_countdown(self):
        """Start countdown for resending OTP"""
        self.stop_countdown()  # Stop any existing countdown
        self.countdown = '60'
        self.resend_timer_active = True
        self.ids.send_otp_button.disabled = True
        self.countdown_event = Clock.schedule_interval(self.update_countdown, 1)
    
    def stop_countdown(self):
        """Stop the countdown timer"""
        if self.countdown_event:
            self.countdown_event.cancel()
            self.countdown_event = None
    
    def update_countdown(self, dt):
        """Update the countdown timer"""
        current = int(self.countdown)
        if current <= 1:
            self.stop_countdown()
            self.resend_timer_active = False
            self.ids.send_otp_button.disabled = False
            self.countdown = '60'
            return False
        
        current -= 1
        self.countdown = str(current)
        return True
    
    def _update_field_states(self):
        """Update all field states based on edit mode"""
        try:
            # Get all input fields
            input_ids = [
                'first_name_input', 'last_name_input', 'email_input', 
                'phone_input', 'dob_input', 'address_input'
            ]
            
            # Update disabled state for all fields
            for field_id in input_ids:
                if hasattr(self.ids, field_id):
                    field = self.ids[field_id]
                    
                    # Set disabled state
                    was_disabled = field.disabled
                    field.disabled = not self.edit_mode
                    print(f"[DEBUG] Changed {field_id}: disabled from {was_disabled} to {field.disabled}")
                else:
                    print(f"[DEBUG] Missing field: {field_id}")
        except Exception as e:
            print(f"[DEBUG] Error updating field states: {str(e)}")
            traceback.print_exc()
    
    def enable_phone_field(self, dt):
        """Special method to handle enabling the phone field properly.
        Uses dt parameter since it's called by Clock.schedule_once."""
        try:
            # Print all properties of the phone input for debugging
            print("[DEBUG] Phone input properties before enabling:")
            print(f"- disabled: {self.ids.phone_input.disabled}")
            print(f"- readonly: {self.ids.phone_input.readonly}")
            print(f"- focus: {self.ids.phone_input.focus}")
            
            # Make sure all properties that could prevent editing are properly set
            self.ids.phone_input.disabled = False
            self.ids.phone_input.readonly = False
            
            # Force focus after a short delay to ensure it's interactive
            Clock.schedule_once(lambda dt: setattr(self.ids.phone_input, 'focus', True), 0.2)
            
            # Reset the binding
            self.ids.phone_input.unbind(text=self.on_phone_input_change)
            self.ids.phone_input.bind(text=self.on_phone_input_change)
            
            # Set hint text
            self.ids.phone_input.hint_text = "Enter your phone number"
            
            # Print updated properties
            print("[DEBUG] Phone input properties after enabling:")
            print(f"- disabled: {self.ids.phone_input.disabled}")
            print(f"- readonly: {self.ids.phone_input.readonly}")
            print(f"- focus: {self.ids.phone_input.focus}")
            
        except Exception as e:
            print(f"[DEBUG] Error enabling phone field: {str(e)}")
            traceback.print_exc()

    def enable_phone_editing(self):
        """Method called when the Edit button next to phone input is clicked"""
        try:
            print("[DEBUG] Phone edit button clicked")
            if not self.edit_mode:
                print("[DEBUG] Not in edit mode, ignoring")
                return
                
            # Store the current value if not already set
            if not self.original_phone:
                self.original_phone = self.ids.phone_input.text.strip() or ""
                
            # Force enable the phone input
            phone_input = self.ids.phone_input
            
            # Print current state for debugging
            print(f"[DEBUG] Phone input before enabling: disabled={phone_input.disabled}, readonly={phone_input.readonly}")
            
            # Make absolutely sure the field is enabled
            phone_input.disabled = False
            phone_input.readonly = False
            
            # Set focus to ensure keyboard appears
            phone_input.focus = True
            
            # Reset appearance if needed
            phone_input.hint_text = "Enter your phone number"
            
            # Print final state
            print(f"[DEBUG] Phone input after enabling: disabled={phone_input.disabled}, readonly={phone_input.readonly}, focused={phone_input.focus}")
            
        except Exception as e:
            print(f"[DEBUG] Error enabling phone editing: {str(e)}")
            traceback.print_exc()
