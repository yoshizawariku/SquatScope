[日本語](README-JP.md) | [English](README.md)

# SquatScope - IMU+EMG BLE Data Receiver

This is a Python application that receives and visualizes IMU (6-axis) and electromyography (EMG) data at 1000 Hz over BLE from the M5StickC Plus2.

About Hardware
https://www.hackster.io/yoshizawa555res/squatscope-3d837a#schematics

## 🔧 Environment

- **Python version**: 3.9.12
- **Environment**: virtual environment (venv)

## 📦 Packages

### BLE
- `bleak` (1.1.0) - cross-platform BLE library
- `pyobjc-framework-CoreBluetooth` (11.1) - macOS CoreBluetooth support

### Data processing & visualization
- `numpy` (2.0.2) - numerical computing
- `pandas` (2.3.1) - data analysis
- `tkinter` - GUI (part of Python standard library)

### Others
- `pyserial` (3.5) - serial communication
- `psutil` (7.0.0) - system information
- `async-timeout` (5.0.1) - async timeout helper

## 🚀 How to use

### 1. Activate virtual environment

```bash
cd your/root/path/SquatScope/Python
# macOS / Linux
source ../venv/bin/activate
# Windows (cmd.exe)
..\venv\Scripts\activate
```

### 2. Run the application

```bash
# Main GUI application
python src/main.py

# Command-line connection test
python test_connection.py
```

### 3. Deactivate the virtual environment

```bash
deactivate
```

## ⚡ System features

### BLE communication (1000 Hz)
- High-rate data reception from M5StickC Plus2
- Binary format (14 bytes/sample × 10 samples/packet)
- Packet loss detection and statistics
- Automatic reconnection handling

### Data processing
- 7 channels: accel (X/Y/Z), gyro (X/Y/Z), and 1 EMG channel
- Real-time filtering: low-pass filter for noise reduction
- Derived metrics: RMS, mean, standard deviation, motion detection
- Buffer management for 1000 samples

### Visualization & UI
- Dark-mode UI
- Real-time graphs
- Connection status and statistics display
- Data save/load functions

## 🔧 For developers

### Adding a new package

```bash
# Activate the virtual environment
source ../venv/bin/activate

# Install package
pip install package_name

# Update requirements.txt
# On Unix/macOS:
pip freeze | grep -E "(bleak|numpy|pandas|pyobjc)" > requirements.txt
# On Windows (cmd.exe):
pip freeze | findstr /R "bleak numpy pandas pyobjc" > requirements.txt
```

### Data format

**Received data structure:**
```
Packet: [2B packet counter] + [14B × 10 samples]
1 sample: accX, accY, accZ, gyroX, gyroY, gyroZ, emg (each int16_t)
```

**Scaling:**
- Accelerometer: ±8G → int16_t (1G = 4096)
- Gyroscope: ±2000 dps → int16_t (1 dps = 16.384)
- EMG: 12-bit ADC value (0–4095)

### Customization points

- Filter coefficient: `filter_alpha` in `data_processor.py`
- Buffer size: `DataProcessor.__init__(buffer_size=1000)`
- Display update intervals: `update_intervals` in `main.py`

## 🐛 Troubleshooting

### BLE connection errors
```bash
# Restart Bluetooth service (macOS)
sudo pkill bluetoothd

# Check device permissions (example)
ls -la /dev/cu.Bluetooth-Incoming-Port
```

### Package errors
```bash
# Upgrade pip
pip install --upgrade pip

# Clear pip cache
pip cache purge

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### High packet loss
1. Reduce distance between devices
2. Stop other 2.4 GHz devices
3. Check BLE connection interval
4. Check MTU negotiation

## 📊 Performance

- Target data rate: 1000 Hz × 7 ch = 7000 samples/s
- Observed packet throughput: ~100 packets/s (10 samples/packet)
- Maximum latency: <20 ms (due to batch transmission)
- Packet loss rate: <1% (under good conditions)

## 📝 License

This project is provided under the MIT License.
```