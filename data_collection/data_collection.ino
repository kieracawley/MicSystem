
#include <ArduinoBLE.h>
#include <PDM.h>
#include <Arduino_BMI270_BMM150.h>

const char* nameOfPeripheral = "MicrophoneMonitor";
const char* uuidOfService = "fff0";
const char* uuidOfAccChar = "fff1";

static const char channels = 1;
static const int frequency = 16000;

short sampleBuffer[512];
volatile int samplesRead;
int micValue = 0;  // Variable to store microphone value


BLEService microphoneService(uuidOfService);

BLECharacteristic accChar(uuidOfAccChar, BLERead | BLENotify | BLEBroadcast, 20);

void setup() {
  Serial.begin(9600);
  while (!Serial);

  startIMU();
  startBLE();
  
  BLE.setLocalName(nameOfPeripheral);
  BLE.setAdvertisedService(microphoneService);
  microphoneService.addCharacteristic(accChar);
  BLE.addService(microphoneService);

  BLE.advertise();

  Serial.println("Bluetooth device active, waiting for connections...");
}

void loop() {
  BLEDevice central = BLE.central();
  if (central) {
    while (central.connected()){
      float x, y, z;
      IMU.readAcceleration(x, y, z);
      String acc = String(x) + ", " + String(y) + ", " + String(z);
      accChar.writeValue(acc.c_str());
      delay(100);

      if (samplesRead) {
        for (int i = 0; i < samplesRead; i++) {
          Serial.println(sampleBuffer[i]);
        }
        samplesRead = 0;      
      }
    }
  }
}

void startIMU() {
  if (!IMU.begin()) {
    Serial.println("Failed to start IMU!");
    while (1);
  }
}

void startBLE() {
  if (!BLE.begin()){
    Serial.println("Failed to start BLE!");
    while (1);
  }
}
