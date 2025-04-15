from kivy.utils import platform
from jnius import autoclass
from threading import Thread
import time

class BluetoothService:
    """Service for handling Bluetooth Low Energy (BLE) operations"""
    
    # Button press event types
    SINGLE_PRESS = "single_press"  # Check-in message
    DOUBLE_PRESS = "double_press"  # Warning message
    TRIPLE_PRESS = "triple_press"  # Emergency message
    
    def __init__(self):
        self.socket = None
        self.is_connected = False
        self.message_callback = None
        self.button_callback = None
        self.message_queue = []
        self.connection_retries = 0
        self.max_retries = 5
        if platform == 'android':
            try:
                self.BluetoothAdapter = autoclass('android.bluetooth.BluetoothAdapter')
                self.UUID = autoclass('java.util.UUID')
                self.adapter = self.BluetoothAdapter.getDefaultAdapter()
            except Exception as e:
                print(f"Error initializing Bluetooth adapter: {e}")
                self.adapter = None
    
    def connect_to_esp32(self, on_message=None):
        """Connect to ESP32 device"""
        if platform != 'android':
            print("Bluetooth is only supported on Android")
            return False
            
        self.message_callback = on_message
        devices = self.adapter.getBondedDevices().toArray()
        
        for device in devices:
            if "ESP" in device.getName():
                try:
                    self.socket = device.createRfcommSocketToServiceRecord(
                        self.UUID.fromString("00001101-0000-1000-8000-00805F9B34FB"))
                    self.socket.connect()
                    self.is_connected = True
                    print("Connected to ESP32")
                    Thread(target=self._listen_for_messages, daemon=True).start()
                    return True
                except Exception as e:
                    print(f"Connection failed: {e}")
                    self.is_connected = False
                    return False
        
        print("ESP32 not found!")
        return False
    
    def connect_to_esp32(self, on_message=None, on_button_press=None):
        """Connect to ESP32 device
        
        Args:
            on_message: Callback for general messages
            on_button_press: Callback for button press events
        """
        if platform != 'android':
            print("Bluetooth is only supported on Android")
            return False
            
        self.message_callback = on_message
        self.button_callback = on_button_press
        devices = self.adapter.getBondedDevices().toArray()
        
        for device in devices:
            if "ESP" in device.getName():
                try:
                    self.socket = device.createRfcommSocketToServiceRecord(
                        self.UUID.fromString("00001101-0000-1000-8000-00805F9B34FB"))
                    self.socket.connect()
                    self.is_connected = True
                    print("Connected to ESP32")
                    Thread(target=self._listen_for_messages, daemon=True).start()
                    return True
                except Exception as e:
                    print(f"Connection failed: {e}")
                    self.is_connected = False
                    return False
        
        print("ESP32 not found!")
        return False
        
    def _listen_for_messages(self):
        """Listen for incoming messages from ESP32"""
        while self.is_connected:
            try:
                if self.socket:
                    data = self.socket.getInputStream().read(1024).decode().strip()
                    if data:
                        # Process button press events
                        if data == "button_press_1":
                            if self.button_callback:
                                self.button_callback(self.SINGLE_PRESS)
                            if self.message_callback:
                                self.message_callback("one_time")
                        elif data == "button_press_2":
                            if self.button_callback:
                                self.button_callback(self.DOUBLE_PRESS)
                            if self.message_callback:
                                self.message_callback("two_time")
                        elif data == "button_press_3":
                            if self.button_callback:
                                self.button_callback(self.TRIPLE_PRESS)
                            if self.message_callback:
                                self.message_callback("three_time")
                        # Handle other messages
                        elif self.message_callback:
                            self.message_callback(data)
            except Exception as e:
                print(f"Error reading message: {e}")
                self.is_connected = False
                self._reconnect()
                break
    
    def _reconnect(self):
        """Attempt to reconnect to ESP32 with retry limits"""
        if self.connection_retries >= self.max_retries:
            print("Max reconnection attempts reached")
            return
            
        self.connection_retries += 1
        print(f"Attempting reconnect ({self.connection_retries}/{self.max_retries})...")
        time.sleep(2 * self.connection_retries)  # Exponential backoff
        
        if self.connect_to_esp32(self.message_callback):
            self.connection_retries = 0  # Reset counter on success
            # Resend any queued messages
    def _process_message_queue(self):
        """Process queued messages after reconnection"""
        while self.is_connected and self.message_queue:
            try:
                message = self.message_queue.pop(0)
                self.socket.getOutputStream().write(message.encode())
                self.socket.getOutputStream().flush()
            except Exception as e:
                print(f"Error sending queued message: {e}")
                self.message_queue.insert(0, message)  # Re-add failed message
                self._reconnect()
                break

            if self.message_queue:
                Thread(target=self._process_message_queue, daemon=True).start()
    
    def disconnect(self):
        """Disconnect from ESP32"""
        if self.socket:
            try:
                self.is_connected = False
                self.socket.close()
                self.socket = None
                print("Disconnected from ESP32")
            except Exception as e:
                print(f"Error disconnecting: {e}")
    
    def send_message(self, message):
        """Send message to ESP32 with queuing"""
        if not self.is_connected or not self.socket:
            print("Queueing message until connection restored")
            self.message_queue.append(message)
            return False
            
        try:
            # Send any queued messages first
            while self.message_queue:
                queued_msg = self.message_queue.pop(0)
                self.socket.getOutputStream().write(queued_msg.encode())
            
            self.socket.getOutputStream().write(message.encode())
            self.socket.getOutputStream().flush()
            return True
        except Exception as e:
            print(f"Error sending message: {e}")
            self.message_queue.append(message)
            self._reconnect()
            return False