from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty
from kivy.clock import Clock
from utils.bluetooth_service import BluetoothService
from utils.permission_handler import PermissionHandler

class BluetoothScreen(Screen):
    """Screen for handling Bluetooth connectivity and messages"""
    
    message_text = StringProperty('Waiting for message...')
    connection_status = StringProperty('Disconnected')
    
    def __init__(self, **kwargs):
        super(BluetoothScreen, self).__init__(**kwargs)
        self.bluetooth_service = BluetoothService()
        self.permission_handler = PermissionHandler()
    
    def on_enter(self):
        """Called when screen is entered"""
        if not self.permission_handler.check_bluetooth_permission():
            self.permission_handler.request_bluetooth_permission(callback=self._on_permission_result)
    
    def _on_permission_result(self, granted):
        """Handle permission request result"""
        if granted:
            self.connect_to_esp32()
        else:
            self.message_text = 'Bluetooth permission denied'
    
    def connect_to_esp32(self):
        """Connect to ESP32 device"""
        def on_message(message):
            """Handle incoming messages from ESP32"""
            if message == 'connected':
                self.connection_status = 'Connected'
                self.message_text = 'Connection established'
            elif message == 'disconnected':
                self.connection_status = 'Disconnected'
                self.message_text = 'Connection lost - retrying...'
            elif message == 'reconnecting':
                self.connection_status = f'Reconnecting ({self.bluetooth_service.connection_retries}/{self.bluetooth_service.max_retries})'
            elif message == 'one_time':
                self.message_text = 'Check-in message sent.'
            elif message == 'two_time':
                self.message_text = 'Warning message sent.'
            elif message == 'three_time':
                self.message_text = 'Emergency message sent!'
        
        def on_button_press(press_type):
            """Handle button press events"""
            if press_type == BluetoothService.SINGLE_PRESS:
                self.message_text = 'Single press detected - Check-in'
            elif press_type == BluetoothService.DOUBLE_PRESS:
                self.message_text = 'Double press detected - Warning'
            elif press_type == BluetoothService.TRIPLE_PRESS:
                self.message_text = 'Triple press detected - Emergency!'
        
        if self.bluetooth_service.connect_to_esp32(on_message, on_button_press):
            self.connection_status = 'Connecting...'
        else:
            self.connection_status = 'Initial connection failed'
            self.message_text = 'Check Bluetooth settings'
    
    def disconnect(self):
        """Disconnect from ESP32"""
        self.bluetooth_service.disconnect()
        self.connection_status = 'Disconnected'
    
    def on_leave(self):
        """Called when screen is exited"""
        self.disconnect()