#include <ArduinoBLE.h>
#include <PDM.h>
#include <Arduino_BMI270_BMM150.h>

// Decive name
const char* nameOfPeripheral = "MicrophoneMonitor";
const char* uuidOfService = "fff0";
const char* uuidOfAccChar = "fff1";

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
      
      Serial.print("X: "); Serial.print(x);
      Serial.print(" Y: "); Serial.print(y);
      Serial.print(" Z: "); Serial.println(z);
      delay(100);
    }
  }
}

void startIMU() {
  if (!IMU.begin()) {
    Serial.println("Failed to initialize IMU!");
    while (1);
  }
}

void startBLE() {
  if (!BLE.begin()){
    Serial.println("Starting BLE failed!");
    while (1);
  }
}
