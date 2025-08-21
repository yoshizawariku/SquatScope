from tkinter import Tk, Frame, Label, Button, Canvas
from tkinter import ttk
import psutil
import datetime
import sys
import math
from collections import deque
from .custom_button import CustomButton
from .components.charts import MultiChannelPlotter, RealTimePlotter

class MainWindow:
    def __init__(self, master):
        self.master = master
        self.master.title("IMU and EMG Data Viewer")
        self.master.geometry("1400x900")
        self.master.configure(bg="#2E2E2E")

        # Buffer for data display
        self.plot_buffer_size = 500
        self.acc_x_data = deque(maxlen=self.plot_buffer_size)
        self.acc_y_data = deque(maxlen=self.plot_buffer_size)
        self.acc_z_data = deque(maxlen=self.plot_buffer_size)
        self.gyro_x_data = deque(maxlen=self.plot_buffer_size)
        self.gyro_y_data = deque(maxlen=self.plot_buffer_size)
        self.gyro_z_data = deque(maxlen=self.plot_buffer_size)
        self.emg_data = deque(maxlen=self.plot_buffer_size)
        self.time_data = deque(maxlen=self.plot_buffer_size)
        
        # Current sensor values
        self.current_data = None
        
        self.create_widgets()

    def create_widgets(self):
        # Header
        self.header_frame = Frame(self.master, bg="#2E2E2E")
        self.header_frame.pack(fill='x', padx=10, pady=5)

        self.title_label = Label(
            self.header_frame, 
            text="IMU and EMG Real-time Data Visualization", 
            bg="#2E2E2E", 
            fg="white", 
            font=("Helvetica", 16)
        )
        self.title_label.pack(pady=10)

        # Main container
        self.main_container = Frame(self.master, bg="#2E2E2E")
        self.main_container.pack(fill='both', expand=True, padx=10, pady=5)

        # Left side: Real-time data display
        self.left_frame = Frame(self.main_container, bg="#3E3E3E", relief="raised", bd=2)
        self.left_frame.pack(side='left', fill='y', padx=(0, 5))
        self.left_frame.config(width=350)
        self.left_frame.pack_propagate(False)

        self.data_title_label = Label(
            self.left_frame,
            text="Real-time Sensor Data",
            bg="#3E3E3E",
            fg="white",
            font=("Arial", 14, "bold")
        )
        self.data_title_label.pack(pady=5)

        # Sensor data display labels
        self.sensor_labels = {}
        sensor_types = ['Acceleration (G)', 'Gyroscope (dps)', 'EMG (ADC)', 'Statistics']
        
        for sensor_type in sensor_types:
            frame = Frame(self.left_frame, bg="#3E3E3E")
            frame.pack(fill='x', padx=10, pady=5)
            
            title = Label(
                frame,
                text=sensor_type,
                bg="#3E3E3E",
                fg="yellow",
                font=("Arial", 12, "bold")
            )
            title.pack(anchor='w')
            
            data_label = Label(
                frame,
                text="Waiting for data...",
                bg="#3E3E3E",
                fg="white",
                font=("Courier", 11),
                justify='left'
            )
            data_label.pack(anchor='w', fill='x')
            
            self.sensor_labels[sensor_type] = data_label

        # Right side: Real-time graph display
        self.right_frame = Frame(self.main_container, bg="#3E3E3E", relief="raised", bd=2)
        self.right_frame.pack(side='right', fill='both', expand=True, padx=(5, 0))

        self.graph_title_label = Label(
            self.right_frame,
            text="Real-time Graph Display",
            bg="#3E3E3E",
            fg="white",
            font=("Arial", 14, "bold")
        )
        self.graph_title_label.pack(pady=5)

        # Graph display mode selection
        self.setup_graph_controls()

        # Graph display area
        self.graph_container = Frame(self.right_frame, bg="#3E3E3E")
        self.graph_container.pack(fill='both', expand=True, padx=5, pady=5)

        # Default is integrated display
        self.current_plotter = None
        self.plotter_mode = "integrated"
        self.switch_plotter_mode("integrated")

        # Footer
        self.footer_frame = Frame(self.master, bg="#2E2E2E")
        self.footer_frame.pack(fill='x', padx=10, pady=5)

        # Control buttons
        button_frame = Frame(self.footer_frame, bg="#2E2E2E")
        button_frame.pack(pady=10)

        self.clear_button = CustomButton(
            button_frame, 
            text="Clear Graph", 
            command=self.clear_graph_data, 
            bg_color="#FFC107", 
            fg_color="black",
            hover_color="#e0a800",
            font=("Arial", 10, "bold"),
            width=100,
            height=30
        )
        self.clear_button.pack(side='left', padx=5)

        # Start system info updates
        self.update_system_info()

    def setup_graph_controls(self):
        """UI setup for graph display controls"""
        control_frame = Frame(self.right_frame, bg="#3E3E3E")
        control_frame.pack(fill='x', padx=5, pady=5)

        Label(control_frame, text="Display Mode:", bg="#3E3E3E", fg="white", 
              font=("Arial", 10)).pack(side='left', padx=5)

        self.integrated_button = CustomButton(
            control_frame,
            text="Integrated",
            command=lambda: self.switch_plotter_mode("integrated"),
            bg_color="#17a2b8",
            fg_color="white",
            hover_color="#138496",
            font=("Arial", 9, "bold"),
            width=80,
            height=25
        )
        self.integrated_button.pack(side='left', padx=2)

        self.emg_button = CustomButton(
            control_frame,
            text="EMG",
            command=lambda: self.switch_plotter_mode("emg"),
            bg_color="#6c757d",
            fg_color="white",
            hover_color="#5a6268",
            font=("Arial", 9, "bold"),
            width=60,
            height=25
        )
        self.emg_button.pack(side='left', padx=2)

        self.acc_button = CustomButton(
            control_frame,
            text="Acceleration",
            command=lambda: self.switch_plotter_mode("acc"),
            bg_color="#6c757d",
            fg_color="white",
            hover_color="#5a6268",
            font=("Arial", 9, "bold"),
            width=80,
            height=25
        )
        self.acc_button.pack(side='left', padx=2)

        self.gyro_button = CustomButton(
            control_frame,
            text="Gyroscope",
            command=lambda: self.switch_plotter_mode("gyro"),
            bg_color="#6c757d",
            fg_color="white",
            hover_color="#5a6268",
            font=("Arial", 9, "bold"),
            width=80,
            height=25
        )
        self.gyro_button.pack(side='left', padx=2)

    def switch_plotter_mode(self, mode):
        """Switch plotter display mode"""
        # Remove existing plotter
        if self.current_plotter:
            for widget in self.graph_container.winfo_children():
                widget.destroy()

        self.plotter_mode = mode
        
        # Update button colors
        self.update_button_colors()

        try:
            if mode == "integrated":
                self.current_plotter = MultiChannelPlotter(
                    self.graph_container,
                    title="Integrated Data Display",
                    figsize=(10, 7)
                )
            elif mode == "emg":
                self.current_plotter = RealTimePlotter(
                    self.graph_container,
                    title="Electromyography (EMG)",
                    ylabel="ADC Value",
                    line_configs=[
                        {'label': 'EMG', 'color': 'red', 'linewidth': 1.5}
                    ],
                    figsize=(10, 4)
                )
            elif mode == "acc":
                self.current_plotter = RealTimePlotter(
                    self.graph_container,
                    title="Acceleration",
                    ylabel="G",
                    line_configs=[
                        {'label': 'X', 'color': 'blue', 'linewidth': 1},
                        {'label': 'Y', 'color': 'green', 'linewidth': 1},
                        {'label': 'Z', 'color': 'red', 'linewidth': 1}
                    ],
                    figsize=(10, 4)
                )
            elif mode == "gyro":
                self.current_plotter = RealTimePlotter(
                    self.graph_container,
                    title="Angular Velocity",
                    ylabel="dps",
                    line_configs=[
                        {'label': 'X', 'color': 'blue', 'linewidth': 1},
                        {'label': 'Y', 'color': 'green', 'linewidth': 1},
                        {'label': 'Z', 'color': 'red', 'linewidth': 1}
                    ],
                    figsize=(10, 4)
                )
        except Exception as e:
            print(f"Plotter creation error: {e}")

    def update_button_colors(self):
        """Update display mode button colors"""
        buttons = {
            "integrated": self.integrated_button,
            "emg": self.emg_button,
            "acc": self.acc_button,
            "gyro": self.gyro_button
        }
        
        for mode, button in buttons.items():
            if mode == self.plotter_mode:
                button.config(bg_color="#17a2b8", hover_color="#138496")
            else:
                button.config(bg_color="#6c757d", hover_color="#5a6268")

    def clear_graph_data(self):
        """Clear graph data"""
        if self.current_plotter:
            self.current_plotter.clear_data()

    def quit_application(self):
        """Exit the application"""
        try:
            # Clear graph data
            if self.current_plotter:
                self.current_plotter.clear_data()
            
            # Close main window
            self.master.quit()
            self.master.destroy()
            
        except Exception as e:
            print(f"Application exit error: {e}")
            # Force exit
            import sys
            sys.exit(0)

    def update_data(self, processed_data):
        """Update and display sensor data"""
        if processed_data is None:
            return
            
        try:
            self.current_data = processed_data
            
            # Add data to buffer
            timestamp = processed_data['timestamp']
            raw_data = processed_data['raw_data']
            filtered_data = processed_data['filtered_data']
            derived_data = processed_data['derived_data']
            
            self.time_data.append(timestamp)
            self.acc_x_data.append(raw_data['acc'][0])
            self.acc_y_data.append(raw_data['acc'][1])
            self.acc_z_data.append(raw_data['acc'][2])
            self.gyro_x_data.append(raw_data['gyro'][0])
            self.gyro_y_data.append(raw_data['gyro'][1])
            self.gyro_z_data.append(raw_data['gyro'][2])
            self.emg_data.append(raw_data['emg'])
            
            # Update display
            self.update_data_display()
            
            # Add data to graph
            self.update_graph_display(timestamp, raw_data)
            
        except Exception as e:
            print(f"Data display error: {e}")

    def update_graph_display(self, timestamp, raw_data):
        """Update graph display"""
        if not self.current_plotter:
            return
            
        try:
            if self.plotter_mode == "integrated":
                self.current_plotter.add_data(
                    timestamp,
                    raw_data['emg'],
                    raw_data['acc'],
                    raw_data['gyro']
                )
            elif self.plotter_mode == "emg":
                self.current_plotter.add_data(timestamp, raw_data['emg'])
            elif self.plotter_mode == "acc":
                self.current_plotter.add_data(
                    timestamp,
                    raw_data['acc'][0],
                    raw_data['acc'][1],
                    raw_data['acc'][2]
                )
            elif self.plotter_mode == "gyro":
                self.current_plotter.add_data(
                    timestamp,
                    raw_data['gyro'][0],
                    raw_data['gyro'][1],
                    raw_data['gyro'][2]
                )
        except Exception as e:
            print(f"Graph update error: {e}")

    def update_data_display(self):
        """Update data display"""
        if self.current_data is None:
            return
            
        try:
            raw_data = self.current_data['raw_data']
            filtered_data = self.current_data['filtered_data']
            derived_data = self.current_data['derived_data']
            
            # Acceleration data display
            acc_text = f"X: {raw_data['acc'][0]:7.3f}  Y: {raw_data['acc'][1]:7.3f}  Z: {raw_data['acc'][2]:7.3f}\n"
            acc_text += f"Filtered:\n"
            acc_text += f"X: {filtered_data['acc'][0]:7.3f}  Y: {filtered_data['acc'][1]:7.3f}  Z: {filtered_data['acc'][2]:7.3f}"
            self.sensor_labels['Acceleration (G)'].config(text=acc_text)
            
            # Gyro data display
            gyro_text = f"X: {raw_data['gyro'][0]:7.1f}  Y: {raw_data['gyro'][1]:7.1f}  Z: {raw_data['gyro'][2]:7.1f}\n"
            gyro_text += f"Filtered:\n"
            gyro_text += f"X: {filtered_data['gyro'][0]:7.1f}  Y: {filtered_data['gyro'][1]:7.1f}  Z: {filtered_data['gyro'][2]:7.1f}"
            self.sensor_labels['Gyroscope (dps)'].config(text=gyro_text)
            
            # EMG data display
            emg_text = f"Raw data: {raw_data['emg']:4d}\n"
            emg_text += f"Filtered: {filtered_data['emg']:7.1f}"
            self.sensor_labels['EMG (ADC)'].config(text=emg_text)
            
            # Statistics display
            stats_text = ""
            if 'acc_magnitude' in derived_data:
                stats_text += f"Acceleration magnitude: {derived_data['acc_magnitude']:.3f} G\n"
            if 'gyro_magnitude' in derived_data:
                stats_text += f"Angular velocity magnitude: {derived_data['gyro_magnitude']:.1f} dps\n"
            if 'emg_rms' in derived_data:
                stats_text += f"EMG RMS: {derived_data['emg_rms']:.1f}\n"
            if 'motion_intensity' in derived_data:
                stats_text += f"Motion intensity: {derived_data['motion_intensity']:.4f}\n"
            if 'muscle_activity_ratio' in derived_data:
                stats_text += f"Muscle activity ratio: {derived_data['muscle_activity_ratio']:.2f}"
            
            if stats_text:
                self.sensor_labels['Statistics'].config(text=stats_text)
            
        except Exception as e:
            print(f"Data display update error: {e}")

    def update_system_info(self):
        """Update system information periodically (small display in the bottom right)"""
        try:
            cpu_usage = psutil.cpu_percent()
            memory_info = psutil.virtual_memory()
            memory_usage = memory_info.percent
            current_time = datetime.datetime.now().strftime("%H:%M:%S")

            # Display system info at the bottom of the left frame
            if hasattr(self, 'system_info_label'):
                self.system_info_label.destroy()
            
            self.system_info_label = Label(
                self.left_frame,
                text=f"Time: {current_time}\nCPU: {cpu_usage:.1f}%\nMemory: {memory_usage:.1f}%",
                bg="#3E3E3E",
                fg="lightgray",
                font=("Arial", 9),
                justify='left'
            )
            self.system_info_label.pack(side='bottom', anchor='sw', padx=5, pady=5)

        except Exception as e:
            print(f"System info update error: {e}")

        # Re-run after 1 second
        self.master.after(1000, self.update_system_info)

if __name__ == "__main__":
    root = Tk()
    app = MainWindow(root)
    root.mainloop()