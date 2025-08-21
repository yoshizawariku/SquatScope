import tkinter as tk
from tkinter import messagebox, ttk
import asyncio
import threading
import sys
import matplotlib
matplotlib.use('TkAgg')  # To use Matplotlib with Tkinter
import matplotlib.pyplot as plt
plt.style.use('dark_background')  # Dark theme setting
from ble_manager import BLEManager
from data_processor import DataProcessor
from ui.main_window import MainWindow
from ui.custom_button import CustomButton
from models.sensor_data import SensorData

class Application:
    def __init__(self, master):
        self.master = master
        self.master.title("IMU+EMG Data Visualizer with Real-time Graphs (1000Hz)")
        self.master.geometry("1400x900")
        self.master.configure(bg="#2E2E2E")  # Dark mode background

        self.ble_manager = BLEManager("M5-IMU-EMG-1000Hz")
        self.data_processor = DataProcessor()
        self.loop = None
        self.ble_thread = None

        # Data statistics
        self.data_count = 0
        self.start_time = None

        # Build UI
        self.setup_ui()
        
        # Set BLE callback
        self.ble_manager.set_data_callback(self.on_data_received)

    def setup_ui(self):
        """Set up UI elements"""
        # Settings to avoid button display issues on macOS
        if sys.platform == "darwin":  # macOS
            self.master.tk.call("ttk::style", "theme", "use", "clam")
        
        # Top control panel
        control_frame = tk.Frame(self.master, bg="#2E2E2E")
        control_frame.pack(fill=tk.X, padx=10, pady=5)

        # Connection button - using custom button
        self.connect_btn = CustomButton(
            control_frame, 
            text="BLE Connect", 
            command=self.toggle_ble_connection,
            bg_color="#4CAF50", 
            fg_color="white",
            hover_color="#45a049",
            font=("Arial", 12, "bold"),
            width=100,
            height=35
        )
        self.connect_btn.pack(side=tk.LEFT, padx=5)

        # Quit button
        self.quit_btn = CustomButton(
            control_frame,
            text="Quit",
            command=self.on_closing,
            bg_color="#DC3545",
            fg_color="white", 
            hover_color="#c82333",
            font=("Arial", 12, "bold"),
            width=80,
            height=35
        )
        self.quit_btn.pack(side=tk.LEFT, padx=5)

        # Status display
        self.status_label = tk.Label(
            control_frame, 
            text="Disconnected", 
            bg="#2E2E2E", 
            fg="red",
            font=("Arial", 12)
        )
        self.status_label.pack(side=tk.LEFT, padx=20)

        # Statistics display
        self.stats_label = tk.Label(
            control_frame,
            text="Data count: 0, Rate: 0 Hz",
            bg="#2E2E2E",
            fg="white",
            font=("Arial", 10)
        )
        self.stats_label.pack(side=tk.RIGHT, padx=5)

        # Main viewer
        self.main_window = MainWindow(master=self.master)
        
        # Override MainWindow's quit_application method to close the entire application
        self.main_window.quit_application = self.on_closing

    def toggle_ble_connection(self):
        """Toggle BLE connection/disconnection"""
        if self.ble_manager.is_connected():
            self.disconnect_ble()
        else:
            self.connect_ble()

    def connect_ble(self):
        """Start BLE connection"""
        self.connect_btn.config(state="disabled", text="Connecting...", 
                               bg_color="#FFA500", hover_color="#FF8C00")
        self.status_label.config(text="Connecting...", fg="orange")
        
        # Start thread for asynchronous BLE processing
        self.ble_thread = threading.Thread(target=self.run_ble_loop, daemon=True)
        self.ble_thread.start()

    def disconnect_ble(self):
        """Disconnect BLE connection"""
        if self.loop and self.ble_manager.is_connected():
            # Execute disconnection as asynchronous task
            asyncio.run_coroutine_threadsafe(
                self.ble_manager.disconnect(), 
                self.loop
            )
        
        self.update_connection_status(False)

    def run_ble_loop(self):
        """Run event loop for BLE processing"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        try:
            self.loop.run_until_complete(self.connect_and_monitor())
        except Exception as e:
            print(f"BLE loop error: {e}")
            self.master.after(0, lambda: self.update_connection_status(False))
        finally:
            self.loop.close()

    async def connect_and_monitor(self):
        """BLE connection and monitoring"""
        try:
            success = await self.ble_manager.connect()
            if success:
                # Execute UI update in main thread
                self.master.after(0, lambda: self.update_connection_status(True))
                
                # Continue loop while connection is maintained
                while self.ble_manager.is_connected():
                    await asyncio.sleep(1)
                    # Periodically update statistics
                    stats = self.ble_manager.get_statistics()
                    self.master.after(0, lambda s=stats: self.update_statistics(s))
            else:
                self.master.after(0, lambda: self.update_connection_status(False))
                
        except Exception as e:
            print(f"BLE connection error: {e}")
            self.master.after(0, lambda: self.update_connection_status(False))

    def update_connection_status(self, connected):
        """Update connection status"""
        if connected:
            self.connect_btn.config(
                text="Disconnect", 
                bg_color="#f44336",
                hover_color="#da190b",
                state="normal"
            )
            self.status_label.config(text="Connected", fg="green")
            self.data_count = 0
            self.start_time = None
        else:
            self.connect_btn.config(
                text="BLE Connect", 
                bg_color="#4CAF50",
                hover_color="#45a049",
                state="normal"
            )
            self.status_label.config(text="Disconnected", fg="red")

    def update_statistics(self, stats):
        """Update statistics"""
        if stats:
            text = f"Packets: {stats['packet_count']}, Lost: {stats['lost_packets']} ({stats['loss_rate']:.1f}%)"
            self.stats_label.config(text=text)

    def on_data_received(self, sensor_data: SensorData):
        """Process when sensor data is received"""
        try:
            # Update data statistics
            self.data_count += 1
            if self.start_time is None:
                import time
                self.start_time = time.time()
            
            # Process data
            processed_data = self.data_processor.process(sensor_data)
            
            # Update UI (execute in main thread)
            self.master.after(0, lambda: self.main_window.update_data(processed_data))
            
            # Calculate and display data rate (every 100 samples)
            if self.data_count % 100 == 0:
                import time
                elapsed = time.time() - self.start_time
                data_rate = self.data_count / elapsed if elapsed > 0 else 0
                text = f"Data count: {self.data_count}, Rate: {data_rate:.1f} Hz"
                self.master.after(0, lambda: self.stats_label.config(text=text))
                
        except Exception as e:
            print(f"Data processing error: {e}")

    def on_closing(self):
        """Process when application is closing"""
        try:
            print("Closing application...")
            if self.ble_manager.is_connected():
                self.disconnect_ble()
            self.master.quit()
            self.master.destroy()
        except Exception as e:
            print(f"Error during closing: {e}")
            # Force exit
            import sys
            sys.exit(0)

if __name__ == "__main__":
    root = tk.Tk()
    app = Application(master=root)
    
    # Handle window close button
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    root.mainloop()