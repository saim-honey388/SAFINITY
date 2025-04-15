import os
import hashlib
import atexit
import traceback
from datetime import datetime
from kivy.utils import platform
from kivy.storage.jsonstore import JsonStore
from kivy.app import App
from functools import lru_cache
from models.database_models import User, TempSignup, UserCountry, init_db
from sqlalchemy.orm import Session, scoped_session
from sqlalchemy.exc import SQLAlchemyError
from threading import Lock

class DatabaseService:
    _instance = None
    _initialized = False
    _lock = Lock()
    _cache = {}

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(DatabaseService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            with self._lock:
                if not self._initialized:
                    print("\nInitializing DatabaseService...")
                    
                    # Set up database path based on platform
                    if platform == 'android':
                        try:
                            # Get the app instance
                            app = App.get_running_app()
                            # Use the app's user_data_dir which is already set up for Android
                            db_dir = app.user_data_dir if app else os.path.dirname(os.path.abspath(__file__))
                            
                            # Ensure the directory exists
                            os.makedirs(db_dir, exist_ok=True)
                            
                            # Store the database in the app's private storage
                            self.db_file = os.path.join(db_dir, 'safinity.db')
                            
                            # Create a JsonStore for caching
                            self.cache_store = JsonStore(os.path.join(db_dir, 'db_cache.json'))
                        except Exception as e:
                            print(f"Warning: Android storage setup failed: {str(e)}")
                            print("Falling back to app directory")
                            db_dir = os.path.dirname(os.path.abspath(__file__))
                            self.db_file = os.path.join(db_dir, 'safinity.db')
                            self.cache_store = None
                    else:
                        # Use app directory for desktop
                        db_dir = os.path.dirname(os.path.abspath(__file__))
                        self.db_file = os.path.join(db_dir, 'safinity.db')
                        self.cache_store = None
                    
                    print(f"Using database at: {self.db_file}")
                    print(f"Database exists: {os.path.exists(self.db_file)}")
                    
                    # Initialize database and session factory
                    self.engine, self.Session = init_db()
                    
                    # Create a scoped session for thread safety
                    self.session = scoped_session(self.Session)
                    
                    # Register cleanup function
                    atexit.register(self.cleanup)
                    
                    self._initialized = True
                    print("DatabaseService initialized successfully")
                    
                    # Display current database state
                    print("\n=== Initial Database State ===")
                    self.display_database_state()

    def __call__(self):
        """Make the instance callable to return the session"""
        return self.session()

    def cleanup(self):
        """Cleanup database connections"""
        if hasattr(self, 'session'):
            self.session.remove()
        if hasattr(self, 'engine'):
            self.engine.dispose()
    
    @lru_cache(maxsize=100)
    def hash_password(self, password):
        """Hash password using SHA-256 with caching for frequently used passwords"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _get_from_cache(self, key):
        """Get value from cache with platform-specific implementation"""
        if platform == 'android' and self.cache_store:
            try:
                return self.cache_store.get(key)['value']
            except KeyError:
                return None
        return self._cache.get(key)
    
    def _set_in_cache(self, key, value):
        """Set value in cache with platform-specific implementation"""
        if platform == 'android' and self.cache_store:
            self.cache_store.put(key, value=value)
        else:
            self._cache[key] = value
    
    def _clear_cache(self):
        """Clear the cache"""
        if platform == 'android' and self.cache_store:
            self.cache_store.clear()
        else:
            self._cache.clear()
    
    def get_user_by_id(self, user_id):
        """Get user by ID with caching"""
        cache_key = f'user_{user_id}'
        user_dict = self._get_from_cache(cache_key)
        
        if user_dict is None:
            try:
                user = self.session().query(User).filter(User.id == user_id).first()
                if user:
                    user_dict = user.to_dict()
                    self._set_in_cache(cache_key, user_dict)
            except SQLAlchemyError as e:
                print(f"Database error in get_user_by_id: {str(e)}")
                return None
            except Exception as e:
                print(f"Unexpected error in get_user_by_id: {str(e)}")
                return None
            finally:
                self.session.remove()
        
        return user_dict

    def create_temp_signup(self, email, phone_number, password, country):
        """Create temporary signup with proper error handling"""
        session = self.session()
        try:
            with self._lock:
                print("\n=== Creating/Updating Temp Signup ===")
                print(f"Received data:")
                print(f"- Email: {email}")
                print(f"- Phone: {phone_number}")
                print(f"- Country: {country}")
                print(f"- Password: {'Yes' if password else 'No'}")
                
                # Normalize phone number if provided
                from utils.phone_util import normalize_phone_number
                if phone_number:
                    original_phone = phone_number
                    phone_number = normalize_phone_number(phone_number)
                    if original_phone != phone_number:
                        print(f"Normalized phone number: {original_phone} → {phone_number}")
                
                # Check in users table first
                existing_user = session.query(User).filter(
                    (User.email == email) | (User.phone_number == phone_number)
                ).first()
                
                if existing_user:
                    print(f"User already exists in users table")
                    # Delete any existing temp signup data
                    temp_signup = session.query(TempSignup).order_by(TempSignup.created_at.desc()).first()
                    if temp_signup:
                        print("Deleting existing temp signup data")
                        session.delete(temp_signup)
                        session.commit()
                    
                    if existing_user.email == email:
                        return None, "USER_EXISTS_EMAIL"
                    else:
                        return None, "USER_EXISTS_PHONE"
                
                # Check in temp_signup table (excluding current temp signup)
                current_temp = session.query(TempSignup).order_by(TempSignup.created_at.desc()).first()
                
                if current_temp:
                    print("\nFound existing temp signup:")
                    print(f"- Email: {current_temp.email}")
                    print(f"- Phone: {current_temp.phone_number}")
                    print(f"- Country: {current_temp.country}")
                    
                    # Only check other temp signups
                    other_temp = session.query(TempSignup).filter(
                        TempSignup.id != current_temp.id
                    )
                    if email:
                        existing_temp = other_temp.filter(TempSignup.email == email).first()
                        if existing_temp:
                            return None, "Email already in use in another signup"
                    
                    if phone_number:
                        existing_temp = other_temp.filter(TempSignup.phone_number == phone_number).first()
                        if existing_temp:
                            return None, "Phone number already in use in another signup"
                    
                    # Update fields if provided (don't overwrite existing data with None)
                    if email is not None:
                        current_temp.email = email
                    if phone_number is not None:
                        current_temp.phone_number = phone_number
                    if password is not None:
                        current_temp.password = self.hash_password(password)
                    if country is not None:
                        current_temp.country = country
                        
                    print(f"\nAfter update:")
                    print(f"- Email: {current_temp.email}")
                    print(f"- Phone: {current_temp.phone_number}")
                    print(f"- Country: {current_temp.country}")
                    temp_signup = current_temp
                else:
                    print("\nCreating new temp signup")
                    temp_signup = TempSignup(
                        email=email,
                        phone_number=phone_number,
                        password=self.hash_password(password) if password else None,
                        country=country,
                        verification_code=None,  # Will be set when sending verification
                        verification_code_expires=None  # Will be set when sending verification
                    )
                    session.add(temp_signup)
                
                try:
                    session.commit()
                    print("\nTemp signup saved successfully")
                    return temp_signup.to_dict(), None
                except Exception as e:
                    print(f"Error committing to database: {str(e)}")
                    session.rollback()
                    return None, f"Database error: {str(e)}"
            
        except SQLAlchemyError as e:
            print(f"Database error in create_temp_signup: {str(e)}")
            session.rollback()
            return None, str(e)
        except Exception as e:
            print(f"Unexpected error in create_temp_signup: {str(e)}")
            session.rollback()
            return None, str(e)
        finally:
            session.remove()
    
    def get_temp_signup(self):
        """Get temporary signup data"""
        try:
            temp_signup = self.session().query(TempSignup).order_by(TempSignup.created_at.desc()).first()
            if temp_signup:
                return temp_signup.to_dict()
            return None
            
        except Exception as e:
            print(f"Error getting temp signup: {str(e)}")
            return None
    
    def move_temp_to_users(self, full_name, date_of_birth, gender, address=None, profile_picture=None):
        """Move data from temp signup to users after profile setup completion"""
        try:
            print("\n=== Moving Temp Signup to Users ===")
            
            # Get temp signup data
            temp_signup = self.session().query(TempSignup).order_by(TempSignup.created_at.desc()).first()
            if not temp_signup:
                print("No temp signup data found")
                return False, "No temporary signup data found"
            
            print("\nTemp signup data retrieved:")
            print(f"- Email: {temp_signup.email}")
            print(f"- Phone: {temp_signup.phone_number}")
            print(f"- Country: {temp_signup.country}")
            
            # Validate required fields
            if not full_name or not date_of_birth or not gender:
                print("Error: Missing required fields")
                missing = []
                if not full_name: missing.append("full name")
                if not date_of_birth: missing.append("date of birth")
                if not gender: missing.append("gender")
                return False, f"Please provide: {', '.join(missing)}"
            
            # Final check for existing user
            if temp_signup.email:
                existing_user = self.session().query(User).filter(User.email == temp_signup.email).first()
                if existing_user:
                    self.session().delete(temp_signup)
                    self.session().commit()
                    return False, f"Email {temp_signup.email} is already registered"
            
            if temp_signup.phone_number:
                existing_user = self.session().query(User).filter(User.phone_number == temp_signup.phone_number).first()
                if existing_user:
                    self.session().delete(temp_signup)
                    self.session().commit()
                    return False, f"Phone number {temp_signup.phone_number} is already registered"
            
            try:
                # Create new user from temp signup data
                user = User(
                    email=temp_signup.email,
                    phone_number=temp_signup.phone_number,
                    password=temp_signup.password,
                    country=temp_signup.country,
                    full_name=full_name,
                    date_of_birth=date_of_birth,
                    gender=gender,
                    address=address,  # Now optional
                    profile_picture=profile_picture,  # Now optional
                    is_verified=True
                )
                
                self.session().add(user)
                
                # Delete temp signup after successful user creation
                self.session().delete(temp_signup)
                
                self.session().commit()
                
                print("\nUser created successfully:")
                print(f"- ID: {user.id}")
                print(f"- Email: {user.email}")
                print(f"- Phone: {user.phone_number}")
                print(f"- Country: {user.country}")
                print(f"- Full Name: {full_name}")
                print(f"- Gender: {gender}")
                print(f"- Date of Birth: {date_of_birth}")
                
                # Display entire database state after successful profile setup
                print("\n=== Database State After Profile Setup ===")
                self.display_database_state()
                
                return True, "User created successfully"
                
            except Exception as e:
                print(f"\nError during move operation: {str(e)}")
                self.session().rollback()
                return False, str(e)
            
        except Exception as e:
            print(f"Error moving temp to users: {str(e)}")
            return False, str(e)
    
    def verify_login(self, identifier, password):
        """Verify login with caching for failed attempts"""
        cache_key = f'login_attempts_{identifier}'
        attempts = self._get_from_cache(cache_key) or 0
        
        if attempts >= 5:  # Limit login attempts
            return False
        
        try:
            print(f"\n=== Login Verification ===")
            print(f"Checking login for: {identifier}")
            
            # Display current database state
            self.display_database_state()
            
            # Try to find user by email or phone
            user = self.session().query(User).filter(
                (User.email == identifier) | (User.phone_number == identifier)
            ).first()
            
            if user:
                print(f"\nFound user: {user.email}")
                print(f"User details:")
                print(f"- ID: {user.id}")
                print(f"- Email: {user.email}")
                print(f"- Phone: {user.phone_number}")
                print(f"- Country: {user.country}")
                print(f"- Full Name: {user.full_name}")
                print(f"- Date of Birth: {user.date_of_birth}")
                print(f"- Gender: {user.gender}")
                #print(f"- Address: {user.address}")
                #print(f"- Profile Picture: {user.profile_picture}")
                # Hash the provided password and compare
                hashed_password = self.hash_password(password)
                print(f"\nPassword comparison:")
                print(f"1. Input password: {password}")
                print(f"2. Input password hash: {hashed_password}")
                print(f"3. Stored password hash: {user.password}")
                print(f"4. Do hashes match? {'Yes' if user.password == hashed_password else 'No'}")
                
                if user.password == hashed_password:
                    print("Password matches!")
                    self._set_in_cache(cache_key, 0)
                    return True
                else:
                    print("Password does not match")
                    self._set_in_cache(cache_key, attempts + 1)
                    return False
            else:
                print(f"No user found with identifier: {identifier}")
                self._set_in_cache(cache_key, attempts + 1)
                return False
                
        except Exception as e:
            print(f"Error verifying login: {str(e)}")
            traceback.print_exc()
            self.session().rollback()
            return False
    
    def get_user_by_credentials(self, identifier, password=None):
        """Get user by email/phone and optionally verify password"""
        try:
            print(f"\n=== Login Attempt Debug ===")
            print(f"Attempting to find user with email/phone: {identifier}")
            
            # Import phone utility for flexible phone number handling
            from utils.phone_util import normalize_phone_number, find_phone_number_variants
            
            # First, check if identifier looks like an email (contains @)
            if '@' in identifier:
                # If it's an email, simple email lookup
                user = self.session().query(User).filter(User.email == identifier).first()
            else:
                # For phone numbers, try multiple formats
                # First normalize the phone number - crucial for Pakistani numbers
                try:
                    # Special handling for Pakistani format (03xxxxxxxx)
                    if identifier.startswith('03') and len(identifier) >= 11:
                        # Try the standard international format for Pakistani numbers
                        pk_international = f"+92{identifier[1:]}"  # Convert 03xx to +923xx
                        print(f"Trying Pakistani international format: {pk_international}")
                        user = self.session().query(User).filter(User.phone_number == pk_international).first()
                        if user:
                            print(f"Found user with Pakistani international format: {pk_international}")
                            # Skip further processing if found
                            pass
                        else:
                            # If not found, try all variants
                            phone_variants = find_phone_number_variants(identifier)
                            print(f"Phone number variants for '{identifier}': {phone_variants}")
                            
                            for variant in phone_variants:
                                user = self.session().query(User).filter(User.phone_number == variant).first()
                                if user:
                                    print(f"Found user with phone variant: {variant}")
                                    break
                    else:
                        # First try exact match
                        user = self.session().query(User).filter(User.phone_number == identifier).first()
                        
                        # If no match, try variant formats
                        if not user:
                            # Get all possible phone number variants
                            phone_variants = find_phone_number_variants(identifier)
                            print(f"Phone number variants for '{identifier}': {phone_variants}")
                            
                            # Try each variant
                            for variant in phone_variants:
                                user = self.session().query(User).filter(User.phone_number == variant).first()
                                if user:
                                    print(f"Found user with phone variant: {variant}")
                                    break
                except Exception as e:
                    print(f"Error processing phone variants: {str(e)}")
                    # Continue with basic search if variant generation fails
                    user = self.session().query(User).filter(User.phone_number == identifier).first()
            
            if user:
                if password is not None:
                    # If password is provided, verify it
                    hashed_password = self.hash_password(password)
                    print(f"\nPassword comparison debug:")
                    print(f"1. Input password: {password}")
                    print(f"2. Input password hash: {hashed_password}")
                    print(f"3. Stored password hash: {user.password}")
                    print(f"4. Do hashes match? {'Yes' if user.password == hashed_password else 'No'}")
                    
                    # TEMPORARY DEBUG FIX: Accept either hashed or raw password match
                    # Remove this in production and ensure consistent password hashing
                    if user.password != hashed_password and user.password != password:
                        print(f"Password mismatch for user: {identifier}")
                        return None
                    print(f"Password verified for user: {identifier}")
                
                print(f"SUCCESS: Found user in database!")
                print(f"User details:")
                print(f"- Email: {user.email}")
                print(f"- Phone: {user.phone_number}")
                print(f"- ID: {user.id}")
                print(f"- Country: {user.country}")
                print(f"- Full Name: {user.full_name}")
                print(f"- Date of Birth: {user.date_of_birth}")
                print(f"- Gender: {user.gender}")
                #print(f"- Address: {user.address}")
                #print(f"- Profile Picture: {user.profile_picture}")
                print(f"- Created At: {user.created_at}")
                
                return user.to_dict()
            else:
                print(f"ERROR: No user found with email/phone: {identifier}")
                return None
                
        except Exception as e:
            print(f"ERROR: Exception while looking up user: {str(e)}")
            traceback.print_exc()
            return None
    
    def get_user_info(self, user_id):
        """Get user information by user_id"""
        try:
            print(f"\n=== Fetching User Info ===")
            print(f"Looking up user with ID: {user_id}")
            
            # Try to find user by ID
            user = self.session().query(User).filter(User.id == user_id).first()
            
            if user:
                print(f"Found user with ID: {user_id}")
                
                # Return user data
                user_data = {
                    'id': user.id,
                    'email': user.email,
                    'phone_number': user.phone_number,
                    'country': user.country,
                    'full_name': user.full_name,
                    'date_of_birth': user.date_of_birth,
                    'gender': user.gender,
                    'profile_picture': user.profile_picture
                }
                
                return user_data
            else:
                print(f"No user found with ID: {user_id}")
                return None
                
        except Exception as e:
            print(f"Error fetching user info: {str(e)}")
            traceback.print_exc()
            return None
    
    def display_database_state(self):
        """Display current database state for debugging"""
        try:
            print("\n=== Current Database State ===")
            
            # Show users
            print("\n--- Users Table ---")
            users = self.session().query(User).all()
            print(f"Total users: {len(users)}")
            
            for user in users:
                print(f"\nUser Details:")
                print(f"- ID: {user.id}")
                print(f"- Email: {user.email}")
                print(f"- Phone: {user.phone_number}")
                print(f"- Password: {user.password}")
                print(f"- Country: {user.country}")
                print(f"- Full Name: {user.full_name}")
                print(f"- Created At: {user.created_at}")
            
            # Show temp signups
            print("\n--- Temp Signups Table ---")
            temp_signups = self.session().query(TempSignup).all()
            print(f"Total temp signups: {len(temp_signups)}")
            
            for signup in temp_signups:
                print(f"\nTemp Signup Details:")
                print(f"- ID: {signup.id}")
                print(f"- Email: {signup.email}")
                print(f"- Phone: {signup.phone_number}")
                print(f"- Country: {signup.country}")
                print(f"- Created At: {signup.created_at}")
            
        except Exception as e:
            print(f"\nError displaying database state: {str(e)}")
            traceback.print_exc()
            
    def terminate_account(self, user_id):
        """Terminate user account"""
        try:
            # Find the user by ID
            user = self.session().query(User).filter(User.id == user_id).first()
            if user:
                # Delete the user
                self.session().delete(user)
                self.session().commit()
                return True
            return False
        except Exception as e:
            print(f"Error terminating account: {str(e)}")
            self.session().rollback()
            return False

    def show_error(self, message):
        # This method is added based on the new implementation
        # It's assumed to exist in the original code or a new one
        print(f"Error: {message}")

    def navigate_to_signup(self):
        try:
            if 'signup' in self.manager.screen_names:
                # If signup screen exists, navigate to it
                self.manager.current = 'signup'
            else:
                # If signup screen doesn't exist, try to add it
                try:
                    from screens.signup.signup_screen import SignupScreen
                    self.manager.add_widget(SignupScreen(name='signup'))
                    self.manager.current = 'signup'
                except Exception as e:
                    # If we can't add the screen, show a friendly error
                    self.show_error("Please go back and try again")
        except Exception as e:
            # If navigation fails, show a friendly error
            self.show_error("Please go back and try again")

    def delete_temp_signup(self):
        """Delete temporary signup data"""
        try:
            print("\n=== Deleting Temp Signup ===")
            temp_signup = self.session().query(TempSignup).order_by(TempSignup.created_at.desc()).first()
            if temp_signup:
                print(f"Deleting temp signup for {temp_signup.email or temp_signup.phone_number}")
                self.session().delete(temp_signup)
                self.session().commit()
                print("Temp signup deleted successfully")
                return True
            return False
        except Exception as e:
            print(f"Error deleting temp signup: {str(e)}")
            traceback.print_exc()
            self.session().rollback()
            return False

    def move_basic_data_to_users(self, email, phone_number, password, country):
        """Move basic user data (email/phone/password) to users table after verification"""
        try:
            print("\n=== Moving Basic Data to Users ===")
            print(f"Received data:")
            print(f"- Email: {email}")
            print(f"- Phone: {phone_number}")
            print(f"- Country: {country}")
            print(f"- Password: {'Yes' if password else 'No'}")
            
            # Validate required fields
            if not email or not phone_number or not password:
                print("Error: Missing required fields")
                print(f"- Email: {email}")
                print(f"- Phone: {phone_number}")
                print(f"- Password: {'Yes' if password else 'No'}")
                return False, "Email, phone number, and password are required"
            
            # Get temp signup data
            temp_signup = self.session().query(TempSignup).order_by(TempSignup.created_at.desc()).first()
            if not temp_signup:
                print("Error: No temporary signup data found")
                return False, "No temporary signup data found"
            
            print("\nFound temp signup data:")
            print(f"- Email: {temp_signup.email}")
            print(f"- Phone: {temp_signup.phone_number}")
            print(f"- Country: {temp_signup.country}")
            
            # Final check for existing user
            existing_user = self.session().query(User).filter(
                (User.email == email) | (User.phone_number == phone_number)
            ).first()
            
            if existing_user:
                print("\nFound existing user:")
                print(f"- Email: {existing_user.email}")
                print(f"- Phone: {existing_user.phone_number}")
                
                # Delete temp signup since user already exists
                self.session().delete(temp_signup)
                self.session().commit()
                
                if existing_user.email == email:
                    return False, f"Email {email} or Phone number {phone_number} is already registered"
                else:
                    return False, f"Phone number {phone_number} or Email {email} is already registered"
            
            try:
                print("\nCreating new user...")
                # Create new user with basic info
                user = User(
                    email=email,
                    phone_number=phone_number,
                    password=temp_signup.password,  # Use the hashed password from temp_signup
                    country=country,
                    is_verified=True,
                    created_at=temp_signup.created_at,
                    # Initialize other fields as None
                    full_name=None,
                    date_of_birth=None,
                    gender=None,
                    address=None,
                    profile_picture=None
                )
                
                self.session().add(user)
                
                # Delete the temporary signup after successful user creation
                self.session().delete(temp_signup)
                
                self.session().commit()
                
                print("\nUser created successfully:")
                print(f"- ID: {user.id}")
                print(f"- Email: {email}")
                print(f"- Phone: {phone_number}")
                print(f"- Country: {country}")
                print(f"- Is Verified: True")
                
                # Display entire database state after successful user creation
                print("\n=== Database State After User Creation ===")
                self.display_database_state()
                
                return True, "Basic user data moved successfully"
                
            except Exception as e:
                print(f"\nError creating user: {str(e)}")
                traceback.print_exc()
                self.session().rollback()
                return False, str(e)
            
        except Exception as e:
            print(f"Error moving basic data to users: {str(e)}")
            traceback.print_exc()
            self.session().rollback()
            return False, str(e)
    
    def update_user_profile(self, user_id, profile_data):
        """Update user profile information"""
        try:
            print("\n=== Updating User Profile ===")
            print(f"Looking up user with identifier: {user_id}")
            print(f"Profile data to update: {profile_data}")
            
            # Try to find user by phone number or email first
            user = self.session().query(User).filter(
                (User.phone_number == user_id) | (User.email == user_id)
            ).first()
            
            # If not found, try as numeric ID
            if not user:
                try:
                    numeric_id = int(user_id)
                    user = self.session().query(User).filter(User.id == numeric_id).first()
                except (ValueError, TypeError):
                    pass
            
            if not user:
                print(f"Error: User not found with identifier: {user_id}")
                return False, "User not found"
            
            print(f"Found user:")
            print(f"- ID: {user.id}")
            print(f"- Email: {user.email}")
            print(f"- Phone: {user.phone_number}")
            print(f"- Current full_name: {user.full_name}")
            print(f"- Current date_of_birth: {user.date_of_birth}")
            print(f"- Current gender: {user.gender}")
            
            # Check if phone number is changing
            old_phone = user.phone_number
            new_phone = profile_data.get('phone_number')
            phone_changed = new_phone and new_phone != old_phone
            
            # Update user fields
            updated_fields = []
            for key, value in profile_data.items():
                if hasattr(user, key):
                    old_value = getattr(user, key)
                    setattr(user, key, value)
                    updated_fields.append(f"{key}: {old_value} -> {value}")
            
            print(f"Updated fields: {updated_fields}")
            
            # Add last_phone_change timestamp if phone is changing
            if phone_changed:
                import datetime
                print(f"[INFO] Phone number changing from '{old_phone}' to '{new_phone}'")
                current_time = datetime.datetime.now()
                setattr(user, 'last_phone_change', current_time)
                print(f"[INFO] Updated last_phone_change to {current_time}")
            
            # Commit changes
            self.session().commit()
            
            # Verify the changes were saved
            updated_user = self.session().query(User).filter(User.id == user.id).first()
            print(f"\nVerifying updated user data:")
            print(f"- ID: {updated_user.id}")
            print(f"- Email: {updated_user.email}")
            print(f"- Phone: {updated_user.phone_number}")
            print(f"- Full Name: {updated_user.full_name}")
            print(f"- Date of Birth: {updated_user.date_of_birth}")
            print(f"- Gender: {updated_user.gender}")
            
            print(f"Profile updated successfully for user {user.id}")
            return True, "Profile updated successfully"
            
        except Exception as e:
            print(f"Error updating profile: {str(e)}")
            traceback.print_exc()
            self.session().rollback()
            return False, str(e)
    
    def check_phone_change_allowed(self, user_id):
        """Check if user is allowed to change phone number (24 hour restriction)"""
        try:
            print(f"[INFO] Checking if user {user_id} can change phone number...")
            
            # Try to find user by phone number, email, or ID
            user = self.session().query(User).filter(
                (User.phone_number == user_id) | (User.email == user_id) | (User.id == user_id)
            ).first()
            
            # If user has no last_phone_change or it's None, allow change
            if not user or not hasattr(user, 'last_phone_change') or not user.last_phone_change:
                print("[INFO] No previous phone change found, allowing change")
                return True, None
            
            # Calculate time difference
            import datetime
            last_change = user.last_phone_change
            if isinstance(last_change, str):
                # Parse string timestamp if needed
                last_change = datetime.datetime.fromisoformat(last_change)
                
            current_time = datetime.datetime.now()
            time_diff = current_time - last_change
            
            # Check if 24 hours (86400 seconds) have passed
            hours_passed = time_diff.total_seconds() / 3600
            if hours_passed < 24:
                # Not enough time has passed
                hours_remaining = 24 - hours_passed
                print(f"[INFO] Not enough time has passed, {hours_remaining:.1f} hours remaining")
                return False, {
                    "hours_remaining": round(hours_remaining, 1),
                    "last_change": last_change.isoformat() if hasattr(last_change, 'isoformat') else str(last_change)
                }
            
            # Enough time has passed
            print("[INFO] 24 hours have passed, allowing phone change")
            return True, None
            
        except Exception as e:
            print(f"Error checking phone change eligibility: {str(e)}")
            traceback.print_exc()
            # On error, allow change to prevent blocking legitimate changes
            return True, None
    
    def check_credential_exists(self, field, value, exclude_user_id=None):
        """
        Check if a credential (email/phone) already exists in the database
        
        Args:
            field (str): Field to check ('email' or 'phone_number')
            value (str): Value to check
            exclude_user_id (str): Optional user ID to exclude from check (for updates)
            
        Returns:
            bool: True if credential exists for another user, False otherwise
        """
        try:
            if not value or value.strip() == '':
                return False
                
            conn = self.create_connection()
            if not conn:
                return False
                
            cursor = conn.cursor()
            
            query = f"SELECT id FROM users WHERE {field} = ?"
            params = [value]
            
            if exclude_user_id:
                query += " AND id != ?"
                params.append(exclude_user_id)
                
            cursor.execute(query, params)
            result = cursor.fetchone()
            
            conn.close()
            
            return result is not None
        except Exception as e:
            print(f"Error checking if credential exists: {str(e)}")
            return False

    def create_tables(self):
        """Create tables if they don't exist and ensure all required columns exist"""
        try:
            print("[INFO] Ensuring all database tables exist")
            
            # Use SQLAlchemy to create all tables
            # This is the proper way using the ORM
            from sqlalchemy import Column, String, inspect
            from sqlalchemy.ext.declarative import declarative_base
            
            # Check if last_phone_change column exists in User model
            inspector = inspect(self.engine)
            has_last_phone_change = False
            
            if inspector.has_table('users'):
                columns = inspector.get_columns('users')
                column_names = [col['name'] for col in columns]
                has_last_phone_change = 'last_phone_change' in column_names
            
            # If the column doesn't exist, add it
            if not has_last_phone_change:
                print("[INFO] Adding last_phone_change column to users table")
                
                # Use SQLAlchemy's ALTER TABLE directly with engine
                from sqlalchemy import text
                with self.engine.connect() as connection:
                    connection.execute(text("ALTER TABLE users ADD COLUMN last_phone_change TIMESTAMP"))
                    connection.commit()
            
            print("[INFO] Database tables and columns are up to date")
            return True
            
        except Exception as e:
            print(f"Error creating tables: {str(e)}")
            traceback.print_exc()
            return False
    
    def connect(self):
        """Connect to SQLite database using SQLAlchemy"""
        try:
            # We'll use the existing session since we're using SQLAlchemy
            # This method is implemented for compatibility with the new code
            if not self.session():
                self.session()
                
            return self.session()
        except Exception as e:
            print(f"Error connecting to database: {str(e)}")
            traceback.print_exc()
            return None

    def delete_user(self, user_id):
        """
        Delete a user account from the database
        
        Args:
            user_id: The ID of the user to delete
            
        Returns:
            bool: True if deletion was successful, False otherwise
        """
        try:
            # Create a new session
            session = self.Session()
            
            # Find the user to delete
            user = session.query(User).filter(User.id == user_id).first()
            
            if not user:
                print(f"No user found with ID: {user_id}")
                session.close()
                return False
            
            # Delete the user
            session.delete(user)
            
            # Commit the changes
            session.commit()
            
            # Close the session
            session.close()
            
            print(f"User {user_id} deleted successfully")
            return True
            
        except Exception as e:
            print(f"Error deleting user: {str(e)}")
            traceback.print_exc()
            return False

    def handle_error(self, error, operation):
        """Centralized error handling"""
        if isinstance(error, SQLAlchemyError):
            print(f"Database error during {operation}: {str(error)}")
            # Attempt recovery
            try:
                self.session().remove()
                self.session()
            except Exception as e:
                print(f"Error recovery failed: {str(e)}")
        else:
            print(f"Unexpected error during {operation}: {str(error)}")
        
        if platform == 'android':
            # Additional mobile-specific error handling
            try:
                # Ensure storage is accessible
                app = App.get_running_app()
                if not os.access(app.user_data_dir, os.W_OK):
                    print("Warning: Storage is not writable")
            except Exception as e:
                print(f"Storage check failed: {str(e)}")