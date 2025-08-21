import asyncio
import struct
from bleak import BleakClient, BleakScanner
from models.sensor_data import SensorData
import time

class BLEManager:
    def __init__(self, device_name="M5-IMU-EMG-1000Hz"):
        self.device_name = device_name
        self.device = None
        self.client = None
        self.connected = False
        self.data_callback = None
        self.packet_count = 0
        self.lost_packets = 0
        self.last_packet_number = None
        
        # BLE UUIDs (same as Arduino side)
        self.SERVICE_UUID = "12345678-1234-1234-1234-123456789abc"
        self.CHARACTERISTIC_UUID = "87654321-4321-4321-4321-cba987654321"

    async def scan_devices(self):
        """Scan for BLE devices"""
        print("Scanning for BLE devices...")
        devices = await BleakScanner.discover()
        target_devices = []
        
        for device in devices:
            if device.name and self.device_name in device.name:
                target_devices.append(device)
                print(f"Found: {device.name} ({device.address})")
        
        return target_devices

    async def connect(self, address=None):
        """Connect to BLE device"""
        try:
            if address is None:
                devices = await self.scan_devices()
                if not devices:
                    print(f"Device '{self.device_name}' not found")
                    return False
                self.device = devices[0]
            else:
                self.device = await BleakScanner.find_device_by_address(address)
                if self.device is None:
                    print(f"Device with address {address} not found")
                    return False

            print(f"Connecting: {self.device.name} ({self.device.address})")
            self.client = BleakClient(self.device.address)
            await self.client.connect()
            
            # MTU negotiation
            try:
                mtu = await self.client.get_mtu()
                print(f"Current MTU: {mtu} bytes")
            except:
                print("Failed to get MTU")

            # Enable notifications
            await self.client.start_notify(self.CHARACTERISTIC_UUID, self.handle_notification)
            
            self.connected = True
            self.packet_count = 0
            self.lost_packets = 0
            self.last_packet_number = None
            
            print("BLE connection successful, starting data reception")
            return True
            
        except Exception as e:
            print(f"Connection error: {e}")
            self.connected = False
            return False

    async def disconnect(self):
        """Disconnect BLE connection"""
        if self.client and self.connected:
            try:
                await self.client.stop_notify(self.CHARACTERISTIC_UUID)
                await self.client.disconnect()
                print("BLE disconnection complete")
            except Exception as e:
                print(f"Disconnection error: {e}")
        
        self.connected = False
        self.client = None

    def handle_notification(self, sender, data):
        """Process BLE notification data"""
        try:
            # Packet analysis: [2B packet number] + [14B × 10 samples]
            if len(data) < 2:
                print("Invalid packet size")
                return
            
            # Get packet number (little endian)
            packet_number = struct.unpack('<H', data[0:2])[0]
            
            # Check for packet loss
            if self.last_packet_number is not None:
                expected = (self.last_packet_number + 1) % 65536
                if packet_number != expected:
                    lost = (packet_number - expected) % 65536
                    self.lost_packets += lost
                    print(f"Packet loss detected: {lost} packets (expected: {expected}, received: {packet_number})")
            
            self.last_packet_number = packet_number
            self.packet_count += 1
            
            # Sensor data analysis
            sample_data = data[2:]  # Data after packet number
            batch_size = len(sample_data) // 14  # 1 sample = 14 bytes
            
            if batch_size == 0:
                return
            
            # Process each sample in the batch
            for i in range(batch_size):
                offset = i * 14
                sample_bytes = sample_data[offset:offset + 14]
                
                if len(sample_bytes) == 14:
                    # struct.unpack: 7 int16_t values (little endian)
                    values = struct.unpack('<7h', sample_bytes)
                    
                    # Restore scaling
                    acc_x = values[0] / 4096.0   # ±8G range
                    acc_y = values[1] / 4096.0
                    acc_z = values[2] / 4096.0
                    gyro_x = values[3] / 16.384  # ±2000dps range
                    gyro_y = values[4] / 16.384
                    gyro_z = values[5] / 16.384
                    emg = values[6]              # 0-4095 ADC value
                    
                    # Create SensorData object
                    sensor_data = SensorData(
                        timestamp=time.time() * 1000,  # milliseconds
                        acc_data=(acc_x, acc_y, acc_z),
                        gyro_data=(gyro_x, gyro_y, gyro_z),
                        emg_data=emg
                    )
                    
                    # Call callback
                    if self.data_callback:
                        self.data_callback(sensor_data)
            
            # Display statistics periodically
            if self.packet_count % 100 == 0:  # Once per second
                print(f"Reception statistics: Packets {self.packet_count}, Lost {self.lost_packets}")
                
        except Exception as e:
            print(f"Data processing error: {e}")

    def set_data_callback(self, callback):
        """Set data reception callback"""
        self.data_callback = callback

    def is_connected(self):
        return self.connected and self.client and self.client.is_connected

    def get_device_name(self):
        return self.device_name

    def get_statistics(self):
        """Get reception statistics"""
        return {
            'packet_count': self.packet_count,
            'lost_packets': self.lost_packets,
            'loss_rate': (self.lost_packets / max(1, self.packet_count + self.lost_packets)) * 100
        }