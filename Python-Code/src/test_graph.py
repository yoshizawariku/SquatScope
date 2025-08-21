#!/usr/bin/env python3
"""
Test script for real-time graph functionality
Generates mock data to test graph display
"""

import tkinter as tk
import time
import math
import threading
import random
from models.sensor_data import SensorData
from data_processor import DataProcessor
from ui.main_window import MainWindow

class TestDataGenerator:
    """Test data generator"""
    
    def __init__(self, callback):
        self.callback = callback
        self.running = False
        self.thread = None
        self.start_time = time.time()
        
    def start(self):
        """Start data generation"""
        self.running = True
        self.thread = threading.Thread(target=self._generate_data, daemon=True)
        self.thread.start()
        
    def stop(self):
        """Stop data generation"""
        self.running = False
        if self.thread:
            self.thread.join()
    
    def _generate_data(self):
        """Generate mock sensor data"""
        sample_count = 0
        
        while self.running:
            current_time = time.time()
            elapsed = current_time - self.start_time
            
            # Generate mock data (50Hz)
            timestamp = int(elapsed * 1000)  # milliseconds
            
            # Acceleration data (gravity + noise + sine wave)
            acc_x = 0.1 * math.sin(elapsed * 2) + random.uniform(-0.05, 0.05)
            acc_y = 0.1 * math.cos(elapsed * 1.5) + random.uniform(-0.05, 0.05)
            acc_z = 1.0 + 0.1 * math.sin(elapsed * 0.5) + random.uniform(-0.05, 0.05)
            
            # Gyro data (angular velocity simulation)
            gyro_x = 10 * math.sin(elapsed * 0.8) + random.uniform(-2, 2)
            gyro_y = 8 * math.cos(elapsed * 1.2) + random.uniform(-2, 2)
            gyro_z = 5 * math.sin(elapsed * 0.3) + random.uniform(-1, 1)
            
            # EMG data (electromyography simulation)
            base_emg = 2048  # ADC center value
            muscle_activity = 200 * (1 + math.sin(elapsed * 0.2))  # Low frequency activity
            noise = random.uniform(-50, 50)
            emg_value = int(base_emg + muscle_activity + noise)
            emg_value = max(0, min(4095, emg_value))  # Limit to 12-bit ADC range
            
            # Create sensor data object
            sensor_data = SensorData(
                timestamp=timestamp,
                acc_data=[acc_x, acc_y, acc_z],
                gyro_data=[gyro_x, gyro_y, gyro_z],
                emg_data=emg_value
            )
            
            # Execute callback
            self.callback(sensor_data)
            
            sample_count += 1
            
            # Generate data at 50Hz
            time.sleep(0.02)

class TestApplication:
    """Test application"""
    
    def __init__(self, master):
        self.master = master
        self.master.title("Real-time Graph Test Application")
        self.master.geometry("1400x900")
        self.master.configure(bg="#2E2E2E")
        
        self.data_processor = DataProcessor()
        self.data_generator = None
        
        # Data statistics
        self.data_count = 0
        self.start_time = None
        
        self.setup_ui()
        
    def setup_ui(self):
        """UI setup"""
        # Control panel
        control_frame = tk.Frame(self.master, bg="#2E2E2E")
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Start/stop button
        self.start_button = tk.Button(
            control_frame,
            text="Start Test Data",
            command=self.toggle_data_generation,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 12, "bold")
        )
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        # Quit button
        self.quit_button = tk.Button(
            control_frame,
            text="Quit",
            command=self.on_closing,
            bg="#DC3545",
            fg="white", 
            font=("Arial", 12, "bold")
        )
        self.quit_button.pack(side=tk.LEFT, padx=5)
        
        # Statistics display
        self.stats_label = tk.Label(
            control_frame,
            text="Data count: 0, Rate: 0 Hz",
            bg="#2E2E2E",
            fg="white",
            font=("Arial", 10)
        )
        self.stats_label.pack(side=tk.RIGHT, padx=5)
        
        # Main window
        self.main_window = MainWindow(master=self.master)
        
        # Override MainWindow's quit_application method to close the entire application
        self.main_window.quit_application = self.on_closing
        
    def toggle_data_generation(self):
        """Start/stop data generation"""
        if self.data_generator is None or not self.data_generator.running:
            self.start_data_generation()
        else:
            self.stop_data_generation()
    
    def start_data_generation(self):
        """Start data generation"""
        self.data_generator = TestDataGenerator(self.on_data_received)
        self.data_generator.start()
        self.start_button.config(text="Stop Test Data", bg="#f44336")
        self.data_count = 0
        self.start_time = time.time()
        print("Test data generation started")
        
    def stop_data_generation(self):
        """Stop data generation"""
        if self.data_generator:
            self.data_generator.stop()
            self.data_generator = None
        self.start_button.config(text="Start Test Data", bg="#4CAF50")
        print("Test data generation stopped")
    
    def on_data_received(self, sensor_data: SensorData):
        """Process received sensor data"""
        try:
            # Update data statistics
            self.data_count += 1
            
            # Process data
            processed_data = self.data_processor.process(sensor_data)
            
            # Update UI (execute in main thread)
            self.master.after(0, lambda: self.main_window.update_data(processed_data))
            
            # Update statistics (every 100 samples)
            if self.data_count % 100 == 0:
                elapsed = time.time() - self.start_time
                data_rate = self.data_count / elapsed if elapsed > 0 else 0
                text = f"Data count: {self.data_count}, Rate: {data_rate:.1f} Hz"
                self.master.after(0, lambda: self.stats_label.config(text=text))
                
        except Exception as e:
            print(f"Data processing error: {e}")
    
    def on_closing(self):
        """Application closing process"""
        try:
            print("Closing application...")
            self.stop_data_generation()
            self.master.quit()
            self.master.destroy()
        except Exception as e:
            print(f"Error during closing: {e}")
            # Force exit
            import sys
            sys.exit(0)

if __name__ == "__main__":
    import matplotlib
    matplotlib.use('TkAgg')
    import matplotlib.pyplot as plt
    plt.style.use('dark_background')
    
    root = tk.Tk()
    app = TestApplication(master=root)
    
    # Handle window close button
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    print("Starting test application...")
    print("Click 'Start Test Data' to begin simulated data generation")
    root.mainloop()
