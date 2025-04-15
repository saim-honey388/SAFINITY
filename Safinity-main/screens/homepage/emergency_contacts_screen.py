from kivy.uix.screenmanager import Screen
from kivy.lang import Builder
from kivy.properties import ObjectProperty, NumericProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.spinner import Spinner
from kivy.uix.button import Button
from utils.contact_service import ContactService
from utils.veevotech_service import VeevotechService
from models.database_models import User, EmergencyContact
from sqlalchemy.orm import Session
from sqlalchemy import create_engine

class EmergencyContactSection(BoxLayout):
    name_input = ObjectProperty(None)
    phone_input = ObjectProperty(None)
    relationship_spinner = ObjectProperty(None)
    section_id = NumericProperty(0)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.relationship_options = ['Friend', 'Family', 'Other']
        
    def clear_fields(self):
        self.name_input.text = ''
        self.phone_input.text = ''
        self.relationship_spinner.text = 'Select Relationship'

class EmergencyContactsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.contact_service = ContactService()
        self.veevotech_service = VeevotechService()
        self.engine = create_engine('sqlite:///safinity.db')
        self.sections = []
        self.max_sections = 5
        
    def on_enter(self):
        self.load_contacts()
        
    def load_contacts(self):
        session = Session(self.engine)
        try:
            user = session.query(User).first()
            if not user:
                return
            contacts = session.query(EmergencyContact).filter(EmergencyContact.user_id == user.id).all()
            for contact in contacts:
                section = self.ids[f'section_{contact.id}']
                section.name_input.text = contact.name
                section.phone_input.text = contact.phone_number
                section.relationship_spinner.text = contact.relationship
        finally:
            session.close()
    
    def show_message(self, message, color=(0.2, 0.7, 0.3, 1)):
        """Show a popup message with the specified color"""
        from kivy.uix.popup import Popup
        from kivy.uix.label import Label
        popup = Popup(title='', content=Label(text=message), size_hint=(None, None), size=(400, 200))
        popup.background_color = color
        popup.open()

    def save_contact(self, section):
        if not section.name_input.text or not section.phone_input.text or section.relationship_spinner.text == 'Select Relationship':
            self.show_message('Please fill in all fields', color=(0.8, 0.2, 0.2, 1))
            return
            
        def on_permission_granted(granted):
            if not granted:
                self.show_message('Contact permission denied. Please grant permission to save contacts.', color=(0.8, 0.2, 0.2, 1))
                return

            session = Session(self.engine)
            try:
                user = session.query(User).first()
                if not user:
                    self.show_message('User not found', color=(0.8, 0.2, 0.2, 1))
                    return
                    
                # Check if contact already exists
                existing_contact = session.query(EmergencyContact).filter_by(
                    phone_number=section.phone_input.text,
                    user_id=user.id
                ).first()
                
                if existing_contact:
                    existing_contact.name = section.name_input.text
                    existing_contact.relationship = section.relationship_spinner.text
                    action = 'updated'
                else:
                    contact = EmergencyContact(
                        name=section.name_input.text,
                        phone_number=section.phone_input.text,
                        relationship=section.relationship_spinner.text,
                        user_id=user.id
                    )
                    session.add(contact)
                    action = 'added'
                
                try:
                    message = f"{user.full_name} with phone number: {user.phone_number} has added you as their emergency contact"
                    self.veevotech_service.send_verification_code(section.phone_input.text)
                    session.commit()
                    self.load_contacts()  # Refresh the contacts list
                    self.show_message(f'Contact successfully {action}')
                    section.clear_fields()
                except Exception as e:
                    session.rollback()
                    self.show_message(f'Failed to send verification: {str(e)}', color=(0.8, 0.2, 0.2, 1))
            except Exception as e:
                session.rollback()
                self.show_message(f'Error saving contact: {str(e)}', color=(0.8, 0.2, 0.2, 1))
            finally:
                session.close()
        
        self.contact_service.request_contact_permissions(callback=on_permission_granted)
    
    def delete_contact(self, section):
        session = Session(self.engine)
        try:
            contact = session.query(EmergencyContact).filter_by(
                name=section.name_input.text,
                phone_number=section.phone_input.text
            ).first()
            if contact:
                session.delete(contact)
                session.commit()
                section.clear_fields()
        finally:
            session.close()
    
    def add_section(self):
        if len(self.sections) < self.max_sections:
            new_section = EmergencyContactSection()
            self.sections.append(new_section)
            self.ids.contacts_container.add_widget(new_section)

Builder.load_file('screens/homepage/emergency_contacts_screen.kv')