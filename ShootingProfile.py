from dataclasses import dataclass

@dataclass
class ShootingProfile:
    shutter_speed: int
    aperture: int
    iso: int