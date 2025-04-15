from utils.contact_service import ContactService
from utils.veevotech_service import VeevotechService
from models.database_models import EmergencyContact, User
from sqlalchemy.orm import Session
import requests
from kivy.utils import platform
if platform == 'android':
    from plyer import gps
import time

class EmergencyContactService:
    def __init__(self):
        self.contact_service = ContactService()
        self.veevotech_service = VeevotechService()
    
    def request_permissions(self, callback=None):
        """Request necessary permissions for contact access"""
        return self.contact_service.request_contact_permissions(callback)
    
    def get_phone_contacts(self):
        """Get all contacts from phone book"""
        return self.contact_service.get_all_contacts()
        
    def send_custom_message(self, session: Session, user_id: int, custom_message: str):
        """Send a custom message to all emergency contacts
        
        Args:
            session: Database session
            user_id: User ID
            custom_message: Custom message to send
        """
        if not session or not user_id:
            return {'status': 'error', 'message': 'Invalid session or user ID'}

        try:
            # Get user and their emergency contacts
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                return {'status': 'error', 'message': 'User not found'}
            
            emergency_contacts = session.query(EmergencyContact).filter(
                EmergencyContact.user_id == user_id
            ).all()
            
            if not emergency_contacts:
                return {'status': 'error', 'message': 'No emergency contacts found'}
            
            # Get location information if available
            location_str = self._get_location()
            
            # Add location to message if available
            message = custom_message + location_str
            
            results = []
            success_count = 0
            for contact in emergency_contacts:
                # Send message through Veevotech
                url = f"{self.veevotech_service.base_url}/sendsms"
                params = {
                    "hash": self.veevotech_service.api_hash,
                    "receivernum": contact.phone_number,
                    "sendernum": "Default",
                    "textmessage": message
                }
                
                try:
                    # Make API request with timeout
                    response = requests.get(url, params=params, timeout=10)
                    response.raise_for_status()
                    
                    # Parse response
                    api_response = response.json() if response.text else {}
                    is_success = response.status_code == 200 and api_response.get('status') != 'error'
                    
                    if is_success:
                        success_count += 1
                    
                    result = {
                        'status': 'success' if is_success else 'error',
                        'message': api_response.get('message', 'Message sent' if is_success else 'Failed to send message')
                    }
                except requests.exceptions.Timeout:
                    result = {'status': 'error', 'message': 'Request timed out'}
                except requests.exceptions.RequestException as e:
                    result = {'status': 'error', 'message': f'API request failed: {str(e)}'}
                except ValueError as e:
                    result = {'status': 'error', 'message': f'Invalid API response: {str(e)}'}
                except Exception as e:
                    result = {'status': 'error', 'message': f'Unexpected error: {str(e)}'}
                
                results.append({
                    'contact_name': contact.name,
                    'phone_number': contact.phone_number,
                    'status': result['status'],
                    'message': result.get('message', '')
                })
            
            overall_status = 'success' if success_count == len(emergency_contacts) else \
                           'partial' if success_count > 0 else 'error'
            
            return {
                'status': overall_status,
                'message': f'Custom messages sent to {success_count} out of {len(emergency_contacts)} contacts',
                'details': results
            }
            
        except Exception as e:
            return {'status': 'error', 'message': f'System error: {str(e)}'}
        finally:
            try:
                session.commit()
            except Exception:
                session.rollback()
                raise
    
    def _get_location(self):
        """Get current location if available"""
        location_str = ""
        if platform == 'android':
            try:
                gps.configure(on_location=lambda **kwargs: None)
                gps.start(minTime=1000, minDistance=0)
                # Wait briefly for GPS to initialize
                time.sleep(2)
                location = gps.get_location()
                if location:
                    lat, lon = location.get('lat', 0), location.get('lon', 0)
                    location_str = f"\nLocation: https://maps.google.com/?q={lat},{lon}"
            except Exception as e:
                print(f"Error getting location: {e}")
            finally:
                try:
                    gps.stop()
                except:
                    pass
        return location_str
    
    def send_emergency_message(self, session: Session, user_id: int, message_type="emergency"):
        """Send emergency message to all emergency contacts
        
        Args:
            session: Database session
            user_id: User ID
            message_type: Type of message (emergency, warning, check, accidental)
        """
        if not session or not user_id:
            return {'status': 'error', 'message': 'Invalid session or user ID'}

        try:
            # Get user and their emergency contacts
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                return {'status': 'error', 'message': 'User not found'}
            
            emergency_contacts = session.query(EmergencyContact).filter(
                EmergencyContact.user_id == user_id
            ).all()
            
            if not emergency_contacts:
                return {'status': 'error', 'message': 'No emergency contacts found'}
            
            # Get location information if available
            location_str = self._get_location()
            
            # Prepare message based on type
            base_message = ""
            if message_type == "emergency":
                base_message = f"EMERGENCY ALERT: {user.full_name} has triggered an emergency alert. "
                base_message += f"Please contact them immediately at {user.phone_number}."
            elif message_type == "warning":
                base_message = f"WARNING: {user.full_name} has triggered a warning alert. "
                base_message += f"Please check on them when possible at {user.phone_number}."
            elif message_type == "check":
                base_message = f"CHECK-IN: {user.full_name} would like you to check on them. "
                base_message += f"Please contact them when convenient at {user.phone_number}."
            elif message_type == "accidental":
                base_message = f"ACCIDENTAL ALERT: {user.full_name}'s previous alert was triggered by mistake. "
                base_message += f"No action is required. The user is safe."
            else:
                base_message = f"ALERT: {user.full_name} has triggered an alert. "
                base_message += f"Please contact them at {user.phone_number}."
            
            # Add location to message if available
            message = base_message + location_str
            
            results = []
            success_count = 0
            for contact in emergency_contacts:
                # Send emergency message through Veevotech
                url = f"{self.veevotech_service.base_url}/sendsms"
                params = {
                    "hash": self.veevotech_service.api_hash,
                    "receivernum": contact.phone_number,
                    "sendernum": "Default",
                    "textmessage": message
                }
                
                try:
                    # Make API request with timeout
                    response = requests.get(url, params=params, timeout=10)
                    response.raise_for_status()
                    
                    # Parse response
                    api_response = response.json() if response.text else {}
                    is_success = response.status_code == 200 and api_response.get('status') != 'error'
                    
                    if is_success:
                        success_count += 1
                    
                    result = {
                        'status': 'success' if is_success else 'error',
                        'message': api_response.get('message', 'Message sent' if is_success else 'Failed to send message')
                    }
                except requests.exceptions.Timeout:
                    result = {'status': 'error', 'message': 'Request timed out'}
                except requests.exceptions.RequestException as e:
                    result = {'status': 'error', 'message': f'API request failed: {str(e)}'}
                except ValueError as e:
                    result = {'status': 'error', 'message': f'Invalid API response: {str(e)}'}
                except Exception as e:
                    result = {'status': 'error', 'message': f'Unexpected error: {str(e)}'}
                
                results.append({
                    'contact_name': contact.name,
                    'phone_number': contact.phone_number,
                    'status': result['status'],
                    'message': result.get('message', '')
                })
            
            overall_status = 'success' if success_count == len(emergency_contacts) else \
                           'partial' if success_count > 0 else 'error'
            
            return {
                'status': overall_status,
                'message': f'Messages sent to {success_count} out of {len(emergency_contacts)} contacts',
                'details': results
            }
            
        except Exception as e:
            return {'status': 'error', 'message': f'System error: {str(e)}'}
        finally:
            try:
                session.commit()
            except Exception:
                session.rollback()
                raise