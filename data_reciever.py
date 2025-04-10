import asyncio
import math
from datetime import datetime
from typing import Any
from aioconsole import ainput
from bleak import BleakClient, discover

DEVICE_NAME = "Nano33BLE_Accel"
SERVICE_UUID = "fff0"
ACC_CHAR_UUID = "fff1"

selected_device = []

class Connection:
    
    client: BleakClient = None
    prev_direction = None
    
    def __init__(
        self,
        loop: asyncio.AbstractEventLoop,
        acc_char: str,
    ):
        self.loop = loop
        self.acc_char = acc_char

        self.last_packet_time = datetime.now()
        self.connected = False
        self.connected_device = None

        self.acc_data = []
        self.acc_timestamps = []
        self.acc_delays = []

    def detect_direction_change(self, data_str: str):
        try:
            x_str, y_str, z_str = data_str.strip().split(",")
            x, y, z = float(x_str), float(y_str), float(z_str)
            current = (x, y, z)

            if hasattr(self, "prev_vector") and self.prev_vector is not None:
                for i in range(3):
                    prev_val = self.prev_vector[i]
                    curr_val = current[i]
                    
                    if prev_val != 0 and curr_val != 0 and (prev_val * curr_val) < 0:
                        if abs(prev_val - curr_val) >= 0.3:
                            axis = ["X", "Y", "Z"][i]
                            print(f"Significant direction change on axis {axis} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (Δ={abs(prev_val - curr_val):.2f})")
                            break

            self.prev_vector = current

        except ValueError:
            print("Invalid data format:", data_str)

    def on_disconnect(self, client: BleakClient, future: asyncio.Future):
        self.connected = False
        print(f"Disconnected from {self.connected_device.name}!")

    async def cleanup(self):
        if self.client:
            await self.client.stop_notify(ACC_CHAR_UUID)
            await self.client.disconnect()

    async def manager(self):
        print("Starting connection manager.")
        while True:
            if self.client:
                await self.connect()
            else:
                await self.select_device()
                await asyncio.sleep(15.0, loop=loop)       

    async def connect(self):
        if self.connected:
            return
        try:
            await self.client.connect()
            self.connected = await self.client.is_connected()
            if self.connected:
                print(F"Connected to {self.connected_device.name}")
                self.client.set_disconnected_callback(self.on_disconnect)
                await self.client.start_notify(
                    self.acc_char, self.notification_handler,
                )
                while True:
                    if not self.connected:
                        break
                    await asyncio.sleep(3.0, loop=loop)
            else:
                print(f"Failed to connect to {self.connected_device.name}")
        except Exception as e:
            print(e)

    async def select_device(self):
        print("Bluetooh LE hardware warming up...")
        await asyncio.sleep(2.0, loop=loop)
        devices = await discover()

        print("Please select device: ")
        for i, device in enumerate(devices):
            print(f"{i}: {device.name}")

        response = -1
        while True:
            response = await ainput("Select device: ")
            try:
                response = int(response.strip())
            except:
                print("Please make valid selection.")
            
            if response > -1 and response < len(devices):
                break
            else:
                print("Please make valid selection.")

        print(f"Connecting to {devices[response].name}")
        self.connected_device = devices[response]
        self.client = BleakClient(devices[response].address, loop=self.loop)

    def record_time_info(self):
        present_time = datetime.now()
        self.acc_timestamps.append(present_time)
        self.acc_delays.append((present_time - self.last_packet_time).microseconds)
        self.last_packet_time = present_time

    def clear_lists(self):
        self.acc_data.clear()
        self.acc_delays.clear()
        self.acc_timestamps.clear()

    def notification_handler(self, sender: str, data: Any):
        self.detect_direction_change(data.decode('utf-8'))
        # print(data.decode('utf-8'))
        # print(print("Formatted:", datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        # self.acc_data.append(str.from_bytes(data, byteorder="big"))
        # self.record_time_info()
        # if len(self.rx_data) >= self.dump_size:
        #     # self.data_dump_handler(self.rx_data, self.rx_timestamps, self.rx_delays)
        #     self.clear_lists()


async def main():
    while True:
        await asyncio.sleep(5)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()

    connection = Connection(
        loop, ACC_CHAR_UUID
    )
    try:
        asyncio.ensure_future(connection.manager())
        asyncio.ensure_future(main())
        loop.run_forever()
    except KeyboardInterrupt:
        print()
        print("User stopped program.")
    finally:
        print("Disconnecting...")
        loop.run_until_complete(connection.cleanup())
