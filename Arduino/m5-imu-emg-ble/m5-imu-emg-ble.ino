#include <M5Unified.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>

/*
  m5-imu-emg-ble.ino
  M5StickC Plus2 IMU + EMG BLE sensor

  Overview:
  - Samples IMU (accelerometer + gyroscope) at 1000 Hz and a single-channel EMG via ADC.
  - Batches 10 samples into a notification packet sent over BLE: [2B packet number] + [14B * 10 samples] = 142 bytes.
  - Uses M5Unified for IMU and display control, and the ESP32 BLE stack for wireless transmission.

  Usage notes:
  - Press BtnA to start IMU calibration. Calibration values are saved to NVS.
  - The code uses M5.Imu built-in calibration routines; manual offsets are commented out.
*/

// Workaround for Arduino IDE ESP32 Board Manager >= v3.3.0
#define CONFIG_IDF_TARGET_ESP32S3

// Calibration constant used for IMU calibration
static constexpr uint32_t calib_value = 100;

// BLE definitions
#define SERVICE_UUID "12345678-1234-1234-1234-123456789abc"
#define CHARACTERISTIC_UUID "87654321-4321-4321-4321-cba987654321"

BLEServer *pServer = NULL;
BLECharacteristic *pCharacteristic = NULL;
bool deviceConnected = false;
bool oldDeviceConnected = false;

// Sensor configuration
const int analogPin = 36;                // Analog pin for EMG sensor
const int SAMPLING_RATE = 1000;          // 1000 Hz sampling rate
const int BATCH_SIZE = 10;               // Send in batches of 10 samples
const int SEND_INTERVAL_MS = BATCH_SIZE; // Batch send interval in ms (10 ms)

// Data structure (14 bytes per sample)
struct SensorSample
{
    int16_t accX, accY, accZ;    // Acceleration x,y,z (6 bytes)
    int16_t gyroX, gyroY, gyroZ; // Gyroscope x,y,z (6 bytes)
    int16_t emg;                 // EMG single channel (2 bytes)
};

// Buffer settings
SensorSample sampleBuffer[BATCH_SIZE];
int bufferIndex = 0;
unsigned long lastSampleTime = 0;
unsigned long lastSendTime = 0;
unsigned long lastDisplayTime = 0;
uint16_t packetNumber = 0;

// IMU offset variables (unused)
// float accOffsetX = 0, accOffsetY = 0, accOffsetZ = 0;
// float gyroOffsetX = 0, gyroOffsetY = 0, gyroOffsetZ = 0;

// Calibration state
static uint8_t calib_countdown = 0;

// Display update interval (ms)
const int DISPLAY_UPDATE_INTERVAL = 200; // Update display every 200 ms

// Forward declarations
void updateDisplay();
void startCalibration();
void updateCalibration(uint32_t c, bool clear = false);
void sampleSensors();
void sendBatchData();
void handleBLEReconnection();

// Server callback class for BLE connection events
class MyServerCallbacks : public BLEServerCallbacks
{
    void onConnect(BLEServer *pServer)
    {
        deviceConnected = true;
        Serial.println("BLE Device Connected");
        updateDisplay();

        // Connection parameters can be tuned here (MTU negotiation handled separately)
        Serial.println("BLE Connection established");
    };

    void onDisconnect(BLEServer *pServer)
    {
        deviceConnected = false;
        Serial.println("BLE Device Disconnected");
        updateDisplay();
    }
};

// IMU calibration helper (based on official samples)
void updateCalibration(uint32_t c, bool clear)
{
    calib_countdown = c;

    if (c == 0)
    {
        clear = true;
    }

    if (clear)
    {
        M5.Display.fillScreen(BLACK);

        if (c)
        { // Start calibration.
            M5.Imu.setCalibration(calib_value, calib_value, calib_value);
        }
        else
        { // Stop calibration. (Continue calibration only for the geomagnetic sensor)
            M5.Imu.setCalibration(0, 0, calib_value);
            // save calibration values.
            M5.Imu.saveOffsetToNVS();
        }
    }

    if (c)
    {
        M5.Display.setCursor(0, 0);
        M5.Display.setTextColor(WHITE, BLUE);
        M5.Display.printf("Calibrating: %d ", c);
    }
}

void startCalibration(void)
{
    updateCalibration(10, true);
}

void setup()
{
    // Initialize M5Unified
    auto cfg = M5.config();
    M5.begin(cfg);
    M5.Display.setRotation(3);
    M5.Display.fillScreen(BLACK);
    M5.Display.setTextColor(WHITE);
    M5.Display.setTextSize(1);

    Serial.begin(115200);
    Serial.println("M5StickC Plus2 IMU+EMG BLE Sensor Starting...");

    // Initialize IMU and check its type
    M5.Imu.begin();
    delay(100);

    const char *name;
    auto imu_type = M5.Imu.getType();
    switch (imu_type)
    {
    case m5::imu_none:
        name = "not found";
        break;
    case m5::imu_sh200q:
        name = "sh200q";
        break;
    case m5::imu_mpu6050:
        name = "mpu6050";
        break;
    case m5::imu_mpu6886:
        name = "mpu6886";
        break;
    case m5::imu_mpu9250:
        name = "mpu9250";
        break;
    case m5::imu_bmi270:
        name = "bmi270";
        break;
    default:
        name = "unknown";
        break;
    };
    Serial.printf("IMU detected: %s\n", name);
    M5.Display.printf("IMU: %s\n", name);

    if (imu_type == m5::imu_none)
    {
        Serial.println("IMU not found!");
        M5.Display.println("IMU Error!");
        for (;;)
        {
            delay(1000);
        }
    }

    // Load calibration from NVS; start calibration if not found
    if (!M5.Imu.loadOffsetFromNVS())
    {
        Serial.println("Calibration data not found. Starting calibration.");
        startCalibration();
    }
    else
    {
        Serial.println("Calibration data loaded.");
    }

    delay(2000); // Pause to show IMU info on display

    // Initialize BLE device
    BLEDevice::init("M5-IMU-EMG-1000Hz");

    // Create BLE server
    pServer = BLEDevice::createServer();
    pServer->setCallbacks(new MyServerCallbacks());

    // Create BLE service
    BLEService *pService = pServer->createService(SERVICE_UUID);

    // Create BLE characteristic (notify)
    pCharacteristic = pService->createCharacteristic(
        CHARACTERISTIC_UUID,
        BLECharacteristic::PROPERTY_READ |
            BLECharacteristic::PROPERTY_NOTIFY);

    // Add descriptor
    pCharacteristic->addDescriptor(new BLE2902());

    // Start service
    pService->start();

    // Configure and start advertising
    BLEAdvertising *pAdvertising = BLEDevice::getAdvertising();
    pAdvertising->addServiceUUID(SERVICE_UUID);
    pAdvertising->setScanResponse(true);
    pAdvertising->setMinPreferred(0x06); // 7.5 ms connection interval
    pAdvertising->setMaxPreferred(0x12); // 22.5 ms connection interval
    BLEDevice::startAdvertising();

    Serial.println("BLE Advertising started. Waiting for connection...");

    updateDisplay();

    // Initialize timestamps
    lastSampleTime = micros();
    lastSendTime = millis();
    lastDisplayTime = millis();
}

void loop()
{
    unsigned long currentMicros = micros();
    unsigned long currentMillis = millis();

    M5.update();

    // BtnA: start calibration
    if (M5.BtnA.wasPressed())
    {
        startCalibration();
        updateDisplay();
    }

    // 1000 Hz sampling (every 1000 microseconds)
    if (currentMicros - lastSampleTime >= 1000)
    {
        // Check IMU update (per official sample approach)
        auto imu_update = M5.Imu.update();
        if (imu_update)
        {
            sampleSensors();
            lastSampleTime = currentMicros;

            bufferIndex++;

            // When buffer is full, send over BLE
            if (bufferIndex >= BATCH_SIZE)
            {
                if (deviceConnected)
                {
                    sendBatchData();
                }
                bufferIndex = 0;
            }
        }
    }

    // Update display periodically
    if (currentMillis - lastDisplayTime >= DISPLAY_UPDATE_INTERVAL)
    {
        updateDisplay();
        lastDisplayTime = currentMillis;
    }

    // Calibration countdown handling
    static uint32_t prev_sec = 0;
    int32_t sec = millis() / 1000;
    if (prev_sec != sec)
    {
        prev_sec = sec;
        if (calib_countdown)
        {
            updateCalibration(calib_countdown - 1);
        }
    }

    // Handle BLE reconnection logic
    handleBLEReconnection();
}

void sampleSensors()
{
    // Get IMU data (official sample method)
    auto imu_data = M5.Imu.getImuData();

    // Per official sample, access like:
    // data.accel.x, data.accel.y, data.accel.z      // acceleration axes
    // data.gyro.x, data.gyro.y, data.gyro.z         // gyro axes

    float accX = imu_data.accel.x;
    float accY = imu_data.accel.y;
    float accZ = imu_data.accel.z;
    float gyroX = imu_data.gyro.x;
    float gyroY = imu_data.gyro.y;
    float gyroZ = imu_data.gyro.z;

    // Use calibrated data (M5.Imu.update() applies calibration automatically)
    // No manual offsets required

    // Read EMG analog value
    int analogValue = analogRead(analogPin);

    // Convert and scale to int16_t
    // Accel: map ±8G range to ±32767
    sampleBuffer[bufferIndex].accX = (int16_t)(accX * 4096);
    sampleBuffer[bufferIndex].accY = (int16_t)(accY * 4096);
    sampleBuffer[bufferIndex].accZ = (int16_t)(accZ * 4096);

    // Gyro: map ±2000 dps range to ±32767
    sampleBuffer[bufferIndex].gyroX = (int16_t)(gyroX * 16.384);
    sampleBuffer[bufferIndex].gyroY = (int16_t)(gyroY * 16.384);
    sampleBuffer[bufferIndex].gyroZ = (int16_t)(gyroZ * 16.384);

    // EMG: store raw 12-bit ADC value (0-4095)
    sampleBuffer[bufferIndex].emg = (int16_t)analogValue;

    // Periodic debug print
    static int debug_counter = 0;
    if (debug_counter++ % 1000 == 0) // roughly once per second
    {
        Serial.printf("IMU: A[%.3f,%.3f,%.3f] G[%.1f,%.1f,%.1f] EMG:%d\n",
                      accX, accY, accZ, gyroX, gyroY, gyroZ, analogValue);
    }
}

void sendBatchData()
{
    // Packet layout: [2B packet number] + [14B × 10 samples] = 142 bytes
    uint8_t packet[2 + (BATCH_SIZE * sizeof(SensorSample))];

    // Store packet number in little-endian
    packet[0] = packetNumber & 0xFF;
    packet[1] = (packetNumber >> 8) & 0xFF;

    // Copy sensor data
    memcpy(&packet[2], sampleBuffer, BATCH_SIZE * sizeof(SensorSample));

    // Send via BLE
    pCharacteristic->setValue(packet, sizeof(packet));
    pCharacteristic->notify();

    packetNumber++;

    // Reduced-frequency debug output
    static int debugCounter = 0;
    if (debugCounter++ % 100 == 0)
    { // roughly once per second
        Serial.printf("Sent packet #%d, Batch size: %d samples\n",
                      packetNumber - 1, BATCH_SIZE);
    }
}

void updateDisplay()
{
    if (calib_countdown > 0)
    {
        // While calibrating, show calibration screen and skip normal display
        return;
    }

    M5.Display.fillScreen(BLACK);
    M5.Display.setCursor(0, 0);
    M5.Display.setTextColor(WHITE);
    M5.Display.println("IMU+EMG BLE 1000Hz");
    M5.Display.println("==================");

    // Connection status
    if (deviceConnected)
    {
        M5.Display.setTextColor(GREEN);
        M5.Display.println("BLE: Connected");
        M5.Display.setTextColor(BLUE);
        M5.Display.printf("Packet: #%d\n", packetNumber);
    }
    else
    {
        M5.Display.setTextColor(RED);
        M5.Display.println("BLE: Advertising...");
    }

    // Display latest raw sensor values
    if (bufferIndex > 0)
    {
        // Fetch and show the latest IMU values
        auto imu_data = M5.Imu.getImuData();

        M5.Display.setTextColor(WHITE);
        M5.Display.printf("A:%.2f,%.2f,%.2f\n",
                          imu_data.accel.x, imu_data.accel.y, imu_data.accel.z);
        M5.Display.printf("G:%.1f,%.1f,%.1f\n",
                          imu_data.gyro.x, imu_data.gyro.y, imu_data.gyro.z);

        SensorSample *sample = &sampleBuffer[bufferIndex - 1];
        M5.Display.printf("EMG: %d\n", sample->emg);
    }

    M5.Display.setTextColor(YELLOW);
    M5.Display.println("BtnA: Calibrate");
}

void handleBLEReconnection()
{
    // Reconnection handling after disconnect
    if (!deviceConnected && oldDeviceConnected)
    {
        delay(500); // allow BLE stack to settle
        pServer->startAdvertising();
        Serial.println("BLE re-advertising started");
        oldDeviceConnected = deviceConnected;
    }

    // When newly connected, reset counters
    if (deviceConnected && !oldDeviceConnected)
    {
        oldDeviceConnected = deviceConnected;
        // Reset packet counter and buffer index
        packetNumber = 0;
        bufferIndex = 0;
    }
}
