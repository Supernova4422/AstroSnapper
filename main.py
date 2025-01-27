import asyncio
import requests

from nicegui import ui
from CameraClient import CameraClient
from ShootingProfile import ShootingProfile

class WebUi:
    def __init__(self):
        self.image_path = 'image_name.jpg'
        self.image_card = None
        self.is_shooting = False
        self.stop_shooting = False
        self.delay = 0
        self.f_number = None
        self.iso_speed_rate = None
        self.shutter_speed = None
        self.cameraClient = CameraClient()

    def _ConnectToCamera(self):
        ui.notify("Not Implemented")

    def _ConfigRow(self):
        try:
            self.cameraClient.WaitUntilReadyToShoot()
            with ui.row():
                with ui.card():
                    shutter_speeds = self.cameraClient.get_shutterSpeeds()
                    self.shutter_speed = shutter_speeds[0]
                    ui.label('Shutter Speed')
                    ui.select(
                        shutter_speeds,
                        value=self.shutter_speed,
                        on_change=self._SetShutterSpeed)

                with ui.card():
                    ui.label('Bulb Shutter Speed')
                    self.bulb_shutter_speed = 60
                    ui.number(
                        label='Bulb Shutter Speed',
                        value=self.bulb_shutter_speed,
                        on_change= self._SetBulbShutterSpeed)

                with ui.card():
                    ui.label('ISO')
                    iso_speed_rates = self.cameraClient.get_isoSpeedRates()
                    self.iso_speed_rate = iso_speed_rates[0]
                    ui.select(
                        iso_speed_rates,
                        value=self.iso_speed_rate,
                        on_change=self._SetIsoSpeedRate)

                with ui.card():
                    ui.label('F-Number')
                    f_numbers = self.cameraClient.get_fnumbers()
                    self.f_number = f_numbers[0]
                    ui.select(
                        f_numbers,
                        value=self.f_number,
                        on_change=self._SetFNumber)

            with ui.row():
                with ui.card():
                    ui.label('Camera')
                    ui.button('Start Shooting', on_click=self._StartShooting)
                    ui.button('Stop Shooting', on_click=self._StopShooting)
                    ui.button('ConfigureCamera', on_click=self.SetCameraToProfile)
                    ui.button('Status', on_click=self.cameraClient._get_status)

            with ui.row():
                with ui.card():
                    self.image_card = ui.image(self.image_path).classes('w-16').props(f"width=1280px height=720px")
                    ui.button('Reload Image', on_click=self.image_card.force_reload)

        except Exception as e: 
            ui.notify(f"Something went wrong: {e}")

    def UpdateImage(self, url: str):
        img_data = requests.get(url).content
        with open(self.image_path, 'wb') as handler:
            handler.write(img_data)


        self.image_card.force_reload()


    def main(self):
        with ui.row():
            with ui.card():
                ui.label('Setup')
                ui.button('Connect to Camera', on_click=self._ConnectToCamera)
                ui.button('Load', on_click=self._ConfigRow)
        ui.run()

    def _SetShutterSpeed(self, result):
        self.shutter_speed = result.value

    def _SetIsoSpeedRate(self, result):
        self.iso_speed_rate = result.value

    def _SetFNumber(self, result):
        self.f_number = result.value

    def _SetBulbShutterSpeed(self, result):
        self.bulb_shutter_speed = result.value

    def SetCameraToProfile(self):
        self.cameraClient.configure_camera(
            self.iso_speed_rate,
            self.f_number,
            self.shutter_speed)

    def GetShootingProfile(self) -> ShootingProfile:
        return ShootingProfile(
            shutter_speed=self.shutter_speed,
            aperture=self.aperture,
            iso=self.iso)

    def _StopShooting(self):
        if self.is_shooting:
            if not self.stop_shooting:
                self.stop_shooting = True
                ui.notify("Stopping Shooting")
            else:
                ui.notify("Already Stopping Shooting")
        else:
            ui.notify("Not Shooting")
    
    async def _StartShooting(self):
        if self.is_shooting:
            ui.notify("Already shooting")
        else:
            self.is_shooting = True
            self.stop_shooting = False

            self.SetCameraToProfile()
            while self.stop_shooting is False:
                if (self.shutter_speed == 'BULB'):
                    await self.cameraClient.take_bulb_photo(self.bulb_shutter_speed)
                else:
                    url = await self.cameraClient.take_photo()
                    self.UpdateImage(url)
                    await asyncio.sleep(1) # This delay is needed so that 'stop shooting' can be checked.
            self.is_shooting = False
            ui.notify("Shooting stopped")

webUi = WebUi()
webUi.main()