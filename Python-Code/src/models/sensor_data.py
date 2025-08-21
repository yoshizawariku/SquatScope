class SensorData:
    def __init__(self, timestamp, acc_data, gyro_data, emg_data):
        self.timestamp = timestamp  # Timestamp
        self.acc_data = acc_data    # Acceleration data (x, y, z)
        self.gyro_data = gyro_data  # Gyroscope data (x, y, z)
        self.emg_data = emg_data    # Electromyography data

    def __repr__(self):
        return (f"SensorData(timestamp={self.timestamp}, "
                f"acc_data={self.acc_data}, "
                f"gyro_data={self.gyro_data}, "
                f"emg_data={self.emg_data})")