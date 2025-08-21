from tkinter import Tk, Frame, Label, Canvas
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np

class DataViewer(Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.init_ui()
        self.data_buffer = {
            'imu': [],
            'emg': []
        }

    def init_ui(self):
        self.master.title("Data Viewer")
        self.master.configure(bg='black')

        self.canvas = Canvas(self.master, bg='black')
        self.canvas.pack(fill='both', expand=True)

        self.label = Label(self.master, text="IMU and EMG Data", bg='black', fg='white')
        self.label.pack(pady=10)

        self.figure = Figure(figsize=(10, 5), dpi=100)
        self.ax1 = self.figure.add_subplot(211)
        self.ax2 = self.figure.add_subplot(212)

        self.canvas_plot = FigureCanvasTkAgg(self.figure, master=self.canvas)
        self.canvas_plot.get_tk_widget().pack(fill='both', expand=True)

        self.ax1.set_title("IMU Data")
        self.ax1.set_xlabel("Time (s)")
        self.ax1.set_ylabel("Acceleration (g)")
        self.ax2.set_title("EMG Data")
        self.ax2.set_xlabel("Time (s)")
        self.ax2.set_ylabel("Voltage (V)")

    def update_data(self, imu_data, emg_data):
        self.data_buffer['imu'].append(imu_data)
        self.data_buffer['emg'].append(emg_data)

        if len(self.data_buffer['imu']) > 100:  # Limit to the last 100 data points
            self.data_buffer['imu'].pop(0)
            self.data_buffer['emg'].pop(0)

        self.plot_data()

    def plot_data(self):
        time = np.arange(len(self.data_buffer['imu']))

        self.ax1.clear()
        self.ax1.plot(time, self.data_buffer['imu'], color='blue')
        self.ax1.set_title("IMU Data")
        self.ax1.set_xlabel("Time (s)")
        self.ax1.set_ylabel("Acceleration (g)")

        self.ax2.clear()
        self.ax2.plot(time, self.data_buffer['emg'], color='red')
        self.ax2.set_title("EMG Data")
        self.ax2.set_xlabel("Time (s)")
        self.ax2.set_ylabel("Voltage (V)")

        self.canvas_plot.draw()