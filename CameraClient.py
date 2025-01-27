import asyncio
import requests
import time
import json
from typing import List


class CameraClient:
    ip = 'http://192.168.122.1:10000'

    def _send_request(self, method, *params):
        print("Sending request:", method, params)
        command = {
            "method": method,
            "params": params,
            "id": 1,
            "version": "1.0"
        }

        url = f'{self.ip}/sony/camera'
        headers = {'Content-Type': 'application/json'}
        payload = json.dumps(command)
        response = requests.post(url, headers=headers, data=payload)
        result = response.json()
        print(result)
        return result

    def _get_status(self):
        status = self._send_request("getAvailableApiList")
        for entry in status['result'][0]:
            entry: str
            if entry.startswith('get'):
                result2 = self._send_request(entry)
                print(entry, result2)
        status = self._send_request(entry)
        return status

    def get_isoSpeedRates(self) -> List[str]:
        result = self._send_request("getAvailableIsoSpeedRate")
        isos: List[str] = result["result"][1]
        return isos[isos.index('AUTO'):]

    def get_shutterSpeeds(self) -> List[str]:
        result = self._send_request("getAvailableShutterSpeed")
        return result["result"][1]
    
    def get_fnumbers(self) -> List[str]:
        result = self._send_request("getAvailableFNumber")
        return result["result"][1]
    
    def configure_camera(self, iso: str, f_number: str, shutter_speed: str):
        self._send_request('setIsoSpeedRate', iso)
        self._send_request('setFNumber', f_number)
        self._send_request('setShutterSpeed', shutter_speed)

    async def take_photo(self):
        await self.WaitUntilReadyToShoot()
        result = self._send_request("actHalfPressShutter")
        result = self._send_request("actTakePicture")
        return result['result'][0][0]

    async def WaitUntilReadyToShoot(self):
        while True:
            result = self._send_request('getEvent', False)
            key = 'cameraStatus'
            print(result)
            if 'id' in result and result['id'] == 1:
                if next(filter(lambda x: x['type'] == key, result['result']))[key] == 'IDLE':
                    return
            else:
                continue
            asyncio.sleep(1)

    async def take_bulb_photo(self, shutter_speed: int):
        await self.WaitUntilReadyToShoot()
        result1 = self._send_request("startBulbShooting")
        await asyncio.sleep(shutter_speed)
        result = self._send_request("stopBulbShooting")
        await self.WaitUntilReadyToShoot()
        result2 = self._send_request("awaitTakePicture")
        result3 = self._send_request("getEvent")
        return result


if __name__ == "__main__":
    cameraClient = CameraClient()
    cameraClient.get_status()
    cameraClient.take_photo()
    time.sleep(2)  # Give it some time to process