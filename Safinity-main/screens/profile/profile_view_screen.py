from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty, BooleanProperty
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from utils.database_service import DatabaseService

class ProfileViewScreen(Screen):
    first_name = ObjectProperty(None)
    last_name = ObjectProperty(None)
    edit_mode = BooleanProperty(False)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._db_service = DatabaseService()
        self._db = self._db_service()  # Get the session
        self._user_id = None
        print("ProfileViewScreen initialized")
    
    def on_enter(self):
        print("ProfileViewScreen entered")
        # Get user_id from the previous screen
        if hasattr(self.manager.get_screen('login'), '_user_id'):
            self._user_id = self.manager.get_screen('login')._user_id
        elif hasattr(self.manager.get_screen('profile_setup'), '_user_id'):
            self._user_id = self.manager.get_screen('profile_setup')._user_id

        if self._user_id:
            self.load_user_data()
        else:
            self.manager.current = 'login'
    
    def load_user_data(self):
        user = self._db_service.get_user_by_credentials(self._user_id)
        if user:
            # Set the text input values
            first_name_input = self.ids.get('first_name_input')
            last_name_input = self.ids.get('last_name_input')
            
            if first_name_input:
                first_name_input.text = user.get('first_name', '') or ''
            if last_name_input:
                last_name_input.text = user.get('last_name', '') or ''
    
    def toggle_edit_mode(self):
        self.edit_mode = not self.edit_mode
        if not self.edit_mode:
            self.save_changes()
    
    def save_changes(self):
        try:
            first_name_input = self.ids.get('first_name_input')
            last_name_input = self.ids.get('last_name_input')

            if not all([first_name_input, last_name_input]):
                self.show_message('Error', 'Failed to access input fields')
                return

            # Update user profile in database
            success, message = self._db_service.update_user_profile(
                self._user_id,
                {
                    'first_name': first_name_input.text,
                    'last_name': last_name_input.text
                }
            )

            if success:
                self.show_message('Success', 'Profile updated successfully!')
            else:
                self.show_message('Error', message or 'Failed to update profile')

        except Exception as e:
            print(f"Save changes error: {e}")
            self.show_message('Error', 'An error occurred while saving changes')
    
    def cancel_edit(self):
        self.edit_mode = False
        self.load_user_data()  # Reload original data
    
    def show_message(self, title, message):
        popup = Popup(
            title=title,
            content=Label(text=message, text_size=(280, None), halign='center'),
            size_hint=(None, None),
            size=(300, 200)
        )
        popup.open()
    
    def back_to_welcome(self):
        self.manager.current = 'welcome'
    
    def on_leave(self):
        """Clean up when leaving the screen"""
        if hasattr(self, '_db'):
            self._db.close() 