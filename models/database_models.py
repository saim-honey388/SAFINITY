from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey, inspect, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from kivy.utils import platform
import os
import traceback
from utils.android_permissions import AndroidPermissions

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=True)
    phone_number = Column(String, unique=True, nullable=True)
    password = Column(String, nullable=True)
    country = Column(String, nullable=True)
    full_name = Column(String, nullable=True)
    date_of_birth = Column(String, nullable=True)
    gender = Column(String, nullable=True)
    address = Column(String, nullable=True)
    profile_picture = Column(String, nullable=True)
    is_verified = Column(Boolean, default=False)
    verification_code = Column(String, nullable=True)
    verification_code_expires = Column(DateTime, nullable=True)
    
    # Relationship with EmergencyContact model
    emergency_contacts = relationship('EmergencyContact', back_populates='user', cascade='all, delete-orphan')
    created_at = Column(DateTime, default=datetime.utcnow)
    last_phone_change = Column(DateTime, nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'phone_number': self.phone_number,
            'password': self.password,
            'country': self.country,
            'full_name': self.full_name,
            'date_of_birth': self.date_of_birth,
            'gender': self.gender,
            'address': self.address,
            'profile_picture': self.profile_picture,
            'is_verified': self.is_verified,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_phone_change': self.last_phone_change.isoformat() if self.last_phone_change else None
        }

class TempSignup(Base):
    __tablename__ = 'temp_signup'
    
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=True)
    phone_number = Column(String, unique=True, nullable=True)
    password = Column(String, nullable=True)
    country = Column(String, nullable=True)
    verification_code = Column(String)
    verification_code_expires = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'phone_number': self.phone_number,
            'password': self.password,
            'country': self.country,
            'verification_code': self.verification_code,
            'verification_code_expires': self.verification_code_expires.isoformat() if self.verification_code_expires else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class EmergencyContact(Base):
    __tablename__ = 'emergency_contacts'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    name = Column(String, nullable=False)
    phone_number = Column(String, nullable=False)
    relation_type = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship('User', back_populates='emergency_contacts')
    
    # Relationship with User model
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'phone_number': self.phone_number,
            'relationship': self.relationship,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class UserCountry(Base):
    __tablename__ = 'user_country'
    
    id = Column(Integer, primary_key=True)
    country_name = Column(String)
    dial_code = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'country_name': self.country_name,
            'dial_code': self.dial_code,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }

def init_db():
    """Initialize database and return engine and session factory"""
    try:
        print("\nInitializing database...")
        
        # Set up database path based on platform
        if platform == 'android':
            from utils.android_permissions import AndroidPermissions
            android_permissions = AndroidPermissions()
            
            def on_storage_permission(granted):
                if not granted:
                    print("Storage permission denied!")
                    print("Please grant storage permission in Android settings")
                    return None, None
                
                try:
                    from kivy.app import App
                    app = App.get_running_app()
                    if not app:
                        print("Error: Kivy app not running")
                        return None, None
                    
                    # Get the private app storage directory
                    db_dir = app.user_data_dir
                    print(f"Android database directory: {db_dir}")
                    
                    # Ensure the directory exists and is writable
                    try:
                        os.makedirs(db_dir, exist_ok=True)
                        test_file = os.path.join(db_dir, 'test_write')
                        with open(test_file, 'w') as f:
                            f.write('test')
                        os.remove(test_file)
                        print("Storage directory is writable")
                    except Exception as e:
                        print(f"Error testing storage directory: {str(e)}")
                        print("Falling back to app's private storage")
                        db_dir = app.get_application_dir()
                        os.makedirs(db_dir, exist_ok=True)
                    
                    db_file = os.path.join(db_dir, 'safinity.db')
                    print(f"Database file path: {db_file}")
                    
                    # Create SQLite URL with proper URI handling for Android
                    db_url = f'sqlite:///{db_file}?uri=true'
                    
                    # Set SQLite pragmas for better Android compatibility
                    engine = create_engine(
                        db_url,
                        connect_args={
                            'check_same_thread': False,
                            'timeout': 30,
                            'isolation_level': 'IMMEDIATE'
                        },
                        echo=True  # Enable logging
                    )
                    
                    # Create session factory
                    Session = sessionmaker(
                        bind=engine,
                        autoflush=True,
                        autocommit=False
                    )
                    
                    # Create tables with error handling
                    try:
                        Base.metadata.create_all(engine)
                        print("Database tables created successfully")
                    except Exception as e:
                        print(f"Error creating tables: {str(e)}")
                        # Try to verify database connection
                        with engine.connect() as conn:
                            result = conn.execute(text("SELECT 1"))
                            print(f"Database connection test: {result.scalar()}")
                    
                    return engine, Session
                    
                except Exception as e:
                    print(f"Error setting up database: {str(e)}")
                    traceback.print_exc()
                    return None, None
            
            # Check and request storage permission
            if not android_permissions.check_permission('storage'):
                print("Requesting storage permission...")
                android_permissions.request_permission('storage', on_storage_permission)
                return None, None  # Will be initialized after permission granted
            
            print("Storage permission already granted")
            return on_storage_permission(True)
            
        else:
            # Desktop setup
            db_dir = os.path.dirname(os.path.abspath(__file__))
            print(f"Desktop database directory: {db_dir}")
            
            db_file = os.path.join(db_dir, 'safinity.db')
            print(f"Database file path: {db_file}")
            
            # Create SQLite URL
            db_url = f'sqlite:///{db_file}'
            
            try:
                # Create engine with appropriate settings
                engine = create_engine(
                    db_url,
                    connect_args={'check_same_thread': False},
                    echo=True
                )
                
                # Create session factory
                Session = sessionmaker(
                    bind=engine,
                    autoflush=True,
                    autocommit=False
                )
                
                # Create tables
                Base.metadata.create_all(engine)
                print("Database tables created successfully")
                
                return engine, Session
            except Exception as e:
                print(f"Error setting up desktop database: {str(e)}")
                traceback.print_exc()
                return None, None
            
    except Exception as e:
        print(f"Error initializing database: {str(e)}")
        traceback.print_exc()
        return None, None

# Remove the duplicate permission handling code that was here before
