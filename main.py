import asyncio
import subprocess
import requests


from nicegui import ui, app
from CameraClient import CameraClient
from ShootingProfile import ShootingProfile

from enum import Enum

class ShootingState(Enum):
    Ready = 1
    Shooting = 1
    Stopping = 2

class WebUi:
    def __init__(self):
        self.image_path = "image_name.jpg"
        self.image_card = None
        self.state = ShootingState.Ready

        self.f_number = None
        self.iso_speed_rate = None
        self.shutter_speed = None
        self.cameraClient = CameraClient()

    def _ConnectToCamera(self):
        ui.notify("Not Implemented")
        cmd = "sudo wifi connect --ad-hoc SSID_Name"
        subprocess.run(cmd)

    def _ConfigRow(self):
        try:
            self.cameraClient.WaitUntilReadyToShoot()
            with ui.row():
                with ui.card():
                    shutter_speeds = self.cameraClient.get_shutterSpeeds()
                    self.shutter_speed = shutter_speeds[0]
                    ui.label("Shutter Speed")
                    ui.select(
                        shutter_speeds,
                        value=self.shutter_speed,
                        on_change=self._SetShutterSpeed,
                    )

                with ui.card():
                    ui.label("Bulb Shutter Speed")
                    self.bulb_shutter_speed = 60
                    ui.number(
                        label="Bulb Shutter Speed",
                        value=self.bulb_shutter_speed,
                        on_change=self._SetBulbShutterSpeed,
                    )

                with ui.card():
                    ui.label("ISO")
                    iso_speed_rates = self.cameraClient.get_isoSpeedRates()
                    self.iso_speed_rate = iso_speed_rates[0]
                    ui.select(
                        iso_speed_rates,
                        value=self.iso_speed_rate,
                        on_change=self._SetIsoSpeedRate,
                    )

                with ui.card():
                    ui.label("F-Number")
                    f_numbers = self.cameraClient.get_fnumbers()
                    self.f_number = f_numbers[0]
                    ui.select(
                        f_numbers, value=self.f_number, on_change=self._SetFNumber
                    )

            with ui.row():
                with ui.card():
                    ui.label("Camera")
                    ui.button("Take One Shot", on_click=self._SingleShot)
                    ui.button("Start Shooting", on_click=self._StartContinuousShooting)
                    ui.button("Stop Shooting", on_click=self._StopShooting)
                    ui.button("ConfigureCamera", on_click=self.SetCameraToProfile)
                    ui.button("Status", on_click=self.cameraClient._get_status)

            with ui.row():
                with ui.card():
                    self.image_card = (
                        ui.image(self.image_path)
                        .classes("w-16")
                        .props(f"width=1280px height=720px")
                    )
                    ui.button("Reload Image", on_click=self.image_card.force_reload)

        except Exception as e:
            ui.notify(f"Something went wrong: {e}")

    def _UpdateImage(self, url: str):
        img_data = requests.get(url).content
        with open(self.image_path, "wb") as handler:
            handler.write(img_data)
        self.image_card.force_reload()

    def main(self):
        with ui.row():
            with ui.card():
                ui.label("Setup")
                ui.button("Shutdown Site", on_click=self._Shutdown)
                ui.button("Connect to Camera", on_click=self._ConnectToCamera)
                ui.button("Load", on_click=self._ConfigRow)
        ui.run()

    def _Shutdown(self):
        ui.notify("Shutting Down")
        app.shutdown()
        self.running = False

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
            self.iso_speed_rate, self.f_number, self.shutter_speed
        )

    def GetShootingProfile(self) -> ShootingProfile:
        return ShootingProfile(
            shutter_speed=self.shutter_speed, aperture=self.aperture, iso=self.iso
        )

    def _StopShooting(self):
        if self.state is ShootingState.Shooting:
            self.state = ShootingState.Stopping
            ui.notify("Stopping Shooting")
        elif self.state is ShootingState.Stopping:
            ui.notify("Already Stopping Shooting")
        elif self.state is ShootingState.Ready:
            ui.notify("Not Shooting")
        else:
            ui.notify("Unknown State")

    async def _TakePhoto(self):
        if self.shutter_speed == "BULB":
            await self.cameraClient.take_bulb_photo(self.bulb_shutter_speed)
        else:
            url = await self.cameraClient.take_photo()
            self._UpdateImage(url)
            # This delay is needed so that 'stop shooting' can be checked.
            await asyncio.sleep(1)

    async def _SingleShot(self):
        await self._StartShooting(False)
    
    async def _StartContinuousShooting(self):
        await self._StartShooting(True)

    async def _StartShooting(self, continuous: bool):
        if self.state is not ShootingState.Ready:
            ui.notify("Already shooting")
        else:
            ui.notify("Starting shooting")
            self.state = ShootingState.Shooting
            self.SetCameraToProfile()
            await self._TakePhoto()
            while continuous and self.state is not ShootingState.Stopping:
                await self._TakePhoto()

            self.state = ShootingState.Ready
            ui.notify("Shooting stopped")

webUi = WebUi()
webUi.main()
