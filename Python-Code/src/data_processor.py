import numpy as np
from collections import deque
from models.sensor_data import SensorData

class DataProcessor:
    def __init__(self, buffer_size=1000):
        self.buffer_size = buffer_size
        
        # Data buffer for each channel (fixed-length queue)
        self.acc_x_buffer = deque(maxlen=buffer_size)
        self.acc_y_buffer = deque(maxlen=buffer_size)
        self.acc_z_buffer = deque(maxlen=buffer_size)
        self.gyro_x_buffer = deque(maxlen=buffer_size)
        self.gyro_y_buffer = deque(maxlen=buffer_size)
        self.gyro_z_buffer = deque(maxlen=buffer_size)
        self.emg_buffer = deque(maxlen=buffer_size)
        self.timestamp_buffer = deque(maxlen=buffer_size)
        
        # Filter parameters
        self.emg_filter_alpha = 0.1  # EMG low-pass filter coefficient
        self.imu_filter_alpha = 0.05  # IMU low-pass filter coefficient
        
        # Store filtered values
        self.filtered_emg = 0
        self.filtered_acc = [0, 0, 0]
        self.filtered_gyro = [0, 0, 0]

    def process(self, sensor_data: SensorData):
        """Process sensor data and add to buffer"""
        try:
            # Add data to buffer
            self.acc_x_buffer.append(sensor_data.acc_data[0])
            self.acc_y_buffer.append(sensor_data.acc_data[1])
            self.acc_z_buffer.append(sensor_data.acc_data[2])
            self.gyro_x_buffer.append(sensor_data.gyro_data[0])
            self.gyro_y_buffer.append(sensor_data.gyro_data[1])
            self.gyro_z_buffer.append(sensor_data.gyro_data[2])
            self.emg_buffer.append(sensor_data.emg_data)
            self.timestamp_buffer.append(sensor_data.timestamp)
            
            # Apply filtering
            self.apply_filters(sensor_data)
            
            # Return processed data
            return {
                'timestamp': sensor_data.timestamp,
                'raw_data': {
                    'acc': sensor_data.acc_data,
                    'gyro': sensor_data.gyro_data,
                    'emg': sensor_data.emg_data
                },
                'filtered_data': {
                    'acc': tuple(self.filtered_acc),
                    'gyro': tuple(self.filtered_gyro),
                    'emg': self.filtered_emg
                },
                'derived_data': self.calculate_derived_metrics()
            }
            
        except Exception as e:
            print(f"Data processing error: {e}")
            return None

    def apply_filters(self, sensor_data: SensorData):
        """Apply various filters"""
        # EMG low-pass filter (noise removal)
        self.filtered_emg = (
            self.emg_filter_alpha * sensor_data.emg_data + 
            (1 - self.emg_filter_alpha) * self.filtered_emg
        )
        
        # Acceleration low-pass filter
        for i in range(3):
            self.filtered_acc[i] = (
                self.imu_filter_alpha * sensor_data.acc_data[i] + 
                (1 - self.imu_filter_alpha) * self.filtered_acc[i]
            )
        
        # Gyro low-pass filter
        for i in range(3):
            self.filtered_gyro[i] = (
                self.imu_filter_alpha * sensor_data.gyro_data[i] + 
                (1 - self.imu_filter_alpha) * self.filtered_gyro[i]
            )

    def calculate_derived_metrics(self):
        """Calculate derived metrics"""
        metrics = {}
        
        try:
            # Acceleration vector magnitude
            if len(self.acc_x_buffer) > 0:
                acc_magnitude = np.sqrt(
                    self.acc_x_buffer[-1]**2 + 
                    self.acc_y_buffer[-1]**2 + 
                    self.acc_z_buffer[-1]**2
                )
                metrics['acc_magnitude'] = acc_magnitude
            
            # Gyro vector magnitude
            if len(self.gyro_x_buffer) > 0:
                gyro_magnitude = np.sqrt(
                    self.gyro_x_buffer[-1]**2 + 
                    self.gyro_y_buffer[-1]**2 + 
                    self.gyro_z_buffer[-1]**2
                )
                metrics['gyro_magnitude'] = gyro_magnitude
            
            # EMG signal statistics (recent 100 samples)
            if len(self.emg_buffer) >= 100:
                recent_emg = list(self.emg_buffer)[-100:]
                metrics['emg_rms'] = np.sqrt(np.mean(np.array(recent_emg)**2))
                metrics['emg_mean'] = np.mean(recent_emg)
                metrics['emg_std'] = np.std(recent_emg)
                metrics['emg_range'] = np.max(recent_emg) - np.min(recent_emg)
            
            # Motion detection (acceleration variation)
            if len(self.acc_x_buffer) >= 10:
                recent_acc_x = list(self.acc_x_buffer)[-10:]
                recent_acc_y = list(self.acc_y_buffer)[-10:]
                recent_acc_z = list(self.acc_z_buffer)[-10:]
                
                acc_x_var = np.var(recent_acc_x)
                acc_y_var = np.var(recent_acc_y)
                acc_z_var = np.var(recent_acc_z)
                
                metrics['motion_intensity'] = acc_x_var + acc_y_var + acc_z_var
                
            # Muscle activity level (EMG signal activity)
            if len(self.emg_buffer) >= 50:
                recent_emg = list(self.emg_buffer)[-50:]
                baseline = np.percentile(recent_emg, 10)  # Bottom 10% as baseline
                active_samples = [x for x in recent_emg if x > baseline + 50]
                metrics['muscle_activity_ratio'] = len(active_samples) / len(recent_emg)
                
        except Exception as e:
            print(f"Derived metrics calculation error: {e}")
        
        return metrics

    def get_buffer_data(self, channel, num_samples=None):
        """Get buffer data for specified channel"""
        buffer_map = {
            'acc_x': self.acc_x_buffer,
            'acc_y': self.acc_y_buffer,
            'acc_z': self.acc_z_buffer,
            'gyro_x': self.gyro_x_buffer,
            'gyro_y': self.gyro_y_buffer,
            'gyro_z': self.gyro_z_buffer,
            'emg': self.emg_buffer,
            'timestamp': self.timestamp_buffer
        }
        
        if channel not in buffer_map:
            return []
        
        buffer = buffer_map[channel]
        if num_samples is None:
            return list(buffer)
        else:
            return list(buffer)[-num_samples:] if len(buffer) >= num_samples else list(buffer)

    def get_current_stats(self):
        """Get current statistics"""
        return {
            'buffer_size': len(self.emg_buffer),
            'sampling_rate': self.estimate_sampling_rate(),
            'filter_settings': {
                'emg_alpha': self.emg_filter_alpha,
                'imu_alpha': self.imu_filter_alpha
            }
        }

    def estimate_sampling_rate(self):
        """Estimate sampling rate"""
        if len(self.timestamp_buffer) < 10:
            return 0
        
        recent_timestamps = list(self.timestamp_buffer)[-10:]
        intervals = [recent_timestamps[i+1] - recent_timestamps[i] 
                    for i in range(len(recent_timestamps)-1)]
        
        if intervals:
            avg_interval = np.mean(intervals) / 1000  # Convert milliseconds to seconds
            return 1.0 / avg_interval if avg_interval > 0 else 0
        
        return 0

    def reset_buffers(self):
        """Reset all buffers"""
        self.acc_x_buffer.clear()
        self.acc_y_buffer.clear()
        self.acc_z_buffer.clear()
        self.gyro_x_buffer.clear()
        self.gyro_y_buffer.clear()
        self.gyro_z_buffer.clear()
        self.emg_buffer.clear()
        self.timestamp_buffer.clear()
        
        # Reset filter state as well
        self.filtered_emg = 0
        self.filtered_acc = [0, 0, 0]
        self.filtered_gyro = [0, 0, 0]