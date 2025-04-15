import requests
import json
import random
import time
from datetime import datetime, timedelta

class VeevotechService:
    def __init__(self):
        self.api_hash = "cb7a018165c3f899e05c692ce428eb64"
        self.base_url = "https://api.veevotech.com/v3"
        self.otp_storage = {}  # Temporary storage for OTPs
        self.otp_expiry = 1  # OTP expiry in minutes

    def generate_otp(self):
        """Generate a 6-digit OTP"""
        return str(random.randint(100000, 999999))

    def send_verification_code(self, phone_number):
        """Send verification code using Veevotech API"""
        try:
            # Generate OTP
            otp = self.generate_otp()
            
            # Prepare message
            message = f"Your Safinity verification code is: {otp}"
            
            # Prepare API request URL with query parameters
            url = f"{self.base_url}/sendsms"
            params = {
                "hash": self.api_hash,
                "receivernum": phone_number,
                "sendernum": "Default",
                "textmessage": message
            }
            
            print(f"Sending SMS with params: {params}")  # Debug print
            
            # Make API request
            response = requests.get(url, params=params)
            print(f"API Response: {response.text}")  # Debug print
            
            if response.status_code == 200:
                # Store OTP with timestamp
                self.otp_storage[phone_number] = {
                    'otp': otp,
                    'timestamp': datetime.now()
                }
                print(f"OTP sent successfully: {otp}")
                return {'status': 'pending', 'message': 'Verification code sent'}
            else:
                print(f"Failed to send OTP: {response.text}")
                return {'status': 'error', 'message': 'Failed to send verification code'}
                
        except Exception as e:
            print(f"Error sending OTP: {str(e)}")
            return {'status': 'error', 'message': str(e)}

    def verify_code(self, phone_number, code):
        """Verify the OTP code"""
        try:
            # Check if we have a stored OTP for this phone number
            if phone_number not in self.otp_storage:
                print(f"No OTP found for phone number: {phone_number}")
                return {'status': 'rejected', 'message': 'No verification code was sent to this number'}
            
            # Get stored OTP data
            otp_data = self.otp_storage.get(phone_number)
            stored_otp = otp_data.get('otp')
            timestamp = otp_data.get('timestamp')
            
            # Check if OTP has expired
            current_time = datetime.now()
            expiry_time = timestamp + timedelta(minutes=self.otp_expiry)
            
            if current_time > expiry_time:
                print(f"OTP expired for phone number: {phone_number}")
                # Remove expired OTP
                del self.otp_storage[phone_number]
                return {'status': 'rejected', 'message': 'Verification code has expired. Please request a new one'}
            
            # Verify OTP
            if code == stored_otp:
                print(f"OTP verified successfully for: {phone_number}")
                # Remove used OTP
                del self.otp_storage[phone_number]
                return {'status': 'approved', 'message': 'Verification successful'}
            else:
                print(f"Invalid OTP for phone number: {phone_number}. Expected: {stored_otp}, Got: {code}")
                return {'status': 'rejected', 'message': 'Invalid verification code'}
                
        except Exception as e:
            print(f"Error verifying OTP: {str(e)}")
            return {'status': 'error', 'message': f'Verification error: {str(e)}'}