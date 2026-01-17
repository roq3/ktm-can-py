# -*- encoding: utf-8 -*-

# decodes messages read from the KTM 790 Duke CAN bus
# Port from Kotlin ktm-can library

import struct
from typing import Iterator, Tuple, Any, Optional


def lo_nibble(b: int) -> int:
    """Extract lower nibble (4 bits) from byte"""
    return b & 0x0F


def hi_nibble(b: int) -> int:
    """Extract higher nibble (4 bits) from byte"""
    return (b >> 4) & 0x0F


def signed12(value: int) -> int:
    """Convert 12-bit value to signed integer (two's complement)"""
    return -(value & 0b100000000000) | (value & 0b011111111111)


def invert(value: int) -> int:
    """Bitwise NOT operation"""
    return (~value & 0xFF)


def parse_big_endian_uint16(high: int, low: int) -> int:
    """Parse 16-bit value big-endian from two bytes"""
    return ((high & 0xFF) << 8) | (low & 0xFF)


class Decoder790(object):
    """Decoder for KTM 790 Duke CAN messages"""

    # CAN ID constants
    CAN_ID_THROTTLE_MODE = 0x120   # Throttle/Mode + RPM (790 Duke)
    CAN_ID_GEAR_CLUTCH = 0x129     # Gear and clutch
    CAN_ID_THROTTLE_STATE = 0x12A  # Throttle state, requested map
    CAN_ID_WHEEL_SPEED = 0x12B     # Wheel speeds, lean/tilt
    CAN_ID_BRAKES = 0x290          # Brakes
    CAN_ID_TC_BUTTON = 0x450       # Traction control button
    CAN_ID_SENSOR = 0x540          # Temperature, sensors
    CAN_ID_KILL_SWITCH = 0x550     # Kill Switch
    CAN_ID_FUEL_LEVEL = 0x552      # Fuel level
    CAN_ID_LIGHTS = 0x650          # LED lights status

    def __init__(self, emit_unmapped: bool = False,
                 enable_assertions: bool = False) -> None:
        super(Decoder790, self).__init__()

        self.emit_unmapped = emit_unmapped
        self.enable_assertions = enable_assertions

    def do_assert(self, condition: bool, msg: Optional[str] = None) -> None:
        if self.enable_assertions:
            assert condition, msg

    def is_known_can_id(self, can_id: int) -> bool:
        """Check if CAN ID is supported"""
        return can_id in [
            self.CAN_ID_THROTTLE_MODE,
            self.CAN_ID_GEAR_CLUTCH,
            self.CAN_ID_THROTTLE_STATE,
            self.CAN_ID_WHEEL_SPEED,
            self.CAN_ID_BRAKES,
            self.CAN_ID_TC_BUTTON,
            self.CAN_ID_SENSOR,
            self.CAN_ID_KILL_SWITCH,
            self.CAN_ID_FUEL_LEVEL,
            self.CAN_ID_LIGHTS
        ]

    def get_can_id_name(self, can_id: int) -> str:
        """Get human-readable name for CAN ID"""
        names = {
            self.CAN_ID_THROTTLE_MODE: "Throttle/Mode",
            self.CAN_ID_GEAR_CLUTCH: "Gear/Clutch",
            self.CAN_ID_THROTTLE_STATE: "Throttle State",
            self.CAN_ID_WHEEL_SPEED: "Wheel/Lean",
            self.CAN_ID_BRAKES: "Brakes",
            self.CAN_ID_TC_BUTTON: "TC Button",
            self.CAN_ID_SENSOR: "Sensor",
            self.CAN_ID_KILL_SWITCH: "Kill Switch",
            self.CAN_ID_FUEL_LEVEL: "Fuel Level",
            self.CAN_ID_LIGHTS: "Lights/LED Status"
        }
        return names.get(can_id, f"Unknown (0x{can_id:02X})")

    def decode(self, msg: Any) -> Iterator[Tuple[int, str, Any]]:
        """Yields (id, key, value) tuples for known data in a Message"""

        if msg.id == self.CAN_ID_THROTTLE_MODE:
            yield from self._decode_throttle_mode(msg)
        elif msg.id == self.CAN_ID_GEAR_CLUTCH:
            yield from self._decode_gear_clutch(msg)
        elif msg.id == self.CAN_ID_THROTTLE_STATE:
            yield from self._decode_throttle_state(msg)
        elif msg.id == self.CAN_ID_WHEEL_SPEED:
            yield from self._decode_wheel_speed(msg)
        elif msg.id == self.CAN_ID_BRAKES:
            yield from self._decode_brakes(msg)
        elif msg.id == self.CAN_ID_TC_BUTTON:
            yield from self._decode_traction_control(msg)
        elif msg.id == self.CAN_ID_SENSOR:
            yield from self._decode_sensor(msg)
        elif msg.id == self.CAN_ID_KILL_SWITCH:
            yield from self._decode_kill_switch(msg)
        elif msg.id == self.CAN_ID_FUEL_LEVEL:
            yield from self._decode_fuel_level(msg)
        elif msg.id == self.CAN_ID_LIGHTS:
            yield from self._decode_lights(msg)
        elif self.emit_unmapped:
            yield msg.id, "unmapped", " ".join([f"{b:02X}" for b in msg.data])

    def _decode_throttle_mode(self, msg: Any) -> Iterator[Tuple[int, str, Any]]:
        """Decode CAN ID 0x120: Throttle/Mode + RPM"""
        # D0, D1 -- engine rpm
        yield msg.id, "rpm", struct.unpack(">H", msg.data[0:2])[0]

        # D2 -- throttle position (0-255)
        yield msg.id, "throttle", msg.data[2]

        # D3 high nibble -- kill switch (bit 7)
        kill_switch = (msg.data[3] & 0b10000000) >> 7
        yield msg.id, "kill_switch", kill_switch == 1

        # D3 low nibble -- throttle map
        throttle_map = lo_nibble(msg.data[3])
        yield msg.id, "throttle_map", throttle_map

    def _decode_gear_clutch(self, msg: Any) -> Iterator[Tuple[int, str, Any]]:
        """Decode CAN ID 0x129: Gear/Clutch"""
        # D0 high nibble -- gear position
        gear = hi_nibble(msg.data[0])
        yield msg.id, "gear", gear

        # D0 bit 3 -- clutch in
        clutch_in = ((msg.data[0] & 0b00001000) >> 3) == 1
        yield msg.id, "clutch_in", clutch_in

    def _decode_throttle_state(self, msg: Any) -> Iterator[Tuple[int, str, Any]]:
        """Decode CAN ID 0x12A: Throttle State"""
        # D0 -- throttle open percentage (0-255)
        yield msg.id, "throttle_open", msg.data[0]

        # D1 -- requested throttle map
        yield msg.id, "requested_throttle_map", msg.data[1]

        # D2 -- ride mode
        yield msg.id, "ride_mode", msg.data[2]

    def _decode_wheel_speed(self, msg: Any) -> Iterator[Tuple[int, str, Any]]:
        """Decode CAN ID 0x12B: Wheel Speed & Lean/Tilt"""
        # D0, D1 -- front wheel speed (big-endian, scale?)
        front_speed = struct.unpack(">H", msg.data[0:2])[0]
        yield msg.id, "front_wheel_speed", front_speed

        # D2, D3 -- rear wheel speed (big-endian, scale?)
        rear_speed = struct.unpack(">H", msg.data[2:4])[0]
        yield msg.id, "rear_wheel_speed", rear_speed

        # D4, D5 -- lean angle (12-bit signed)
        lean_raw = parse_big_endian_uint16(msg.data[4], msg.data[5]) & 0xFFF
        lean_angle = signed12(lean_raw) / 10.0  # Scale to degrees
        yield msg.id, "lean_angle", lean_angle

        # D6, D7 -- tilt angle (12-bit signed)
        tilt_raw = parse_big_endian_uint16(msg.data[6], msg.data[7]) & 0xFFF
        tilt_angle = signed12(tilt_raw) / 10.0  # Scale to degrees
        yield msg.id, "tilt_angle", tilt_angle

    def _decode_brakes(self, msg: Any) -> Iterator[Tuple[int, str, Any]]:
        """Decode CAN ID 0x290: Brakes"""
        # D0, D1 -- front brake pressure
        front_brake = struct.unpack(">H", msg.data[0:2])[0]
        yield msg.id, "front_brake_pressure", front_brake

        # D2, D3 -- rear brake pressure
        rear_brake = struct.unpack(">H", msg.data[2:4])[0]
        yield msg.id, "rear_brake_pressure", rear_brake

    def _decode_traction_control(self, msg: Any) -> Iterator[Tuple[int, str, Any]]:
        """Decode CAN ID 0x450: Traction Control Button"""
        # D0 bit 0 -- traction control button pressed
        tc_button = (msg.data[0] & 0b00000001) == 1
        yield msg.id, "traction_control_button", tc_button

    def _decode_sensor(self, msg: Any) -> Iterator[Tuple[int, str, Any]]:
        """Decode CAN ID 0x540: Sensors"""
        # D0, D1 -- engine rpm (duplicate from 0x120)
        yield msg.id, "rpm", struct.unpack(">H", msg.data[0:2])[0]

        # D2 -- gear position (duplicate from 0x129)
        yield msg.id, "gear", lo_nibble(msg.data[2])

        # D3 bit 0 -- kickstand up
        kickstand_up = (msg.data[3] & 0b00000001) == 1
        yield msg.id, "kickstand_up", kickstand_up

        # D3 bit 7 -- kickstand error
        kickstand_err = ((msg.data[3] & 0b10000000) >> 7) == 1
        yield msg.id, "kickstand_err", kickstand_err

        # D5 must be 0x00
        self.do_assert(msg.data[4] == 0x00, "D5 must be 0x00")

        # D6, D7 -- coolant temperature (°C)
        coolant_temp = struct.unpack(">H", msg.data[5:7])[0] / 10.0
        yield msg.id, "coolant_temp", coolant_temp

    def _decode_kill_switch(self, msg: Any) -> Iterator[Tuple[int, str, Any]]:
        """Decode CAN ID 0x550: Kill Switch"""
        # D0 bit 0 -- kill switch on
        kill_switch_on = (msg.data[0] & 0b00000001) == 1
        yield msg.id, "kill_switch_on", kill_switch_on

    def _decode_fuel_level(self, msg: Any) -> Iterator[Tuple[int, str, Any]]:
        """Decode CAN ID 0x552: Fuel Level"""
        # D0 -- fuel level (0-255, scale to percentage)
        fuel_level = msg.data[0] / 2.55  # Convert to percentage
        yield msg.id, "fuel_level_percent", fuel_level

    def _decode_lights(self, msg: Any) -> Iterator[Tuple[int, str, Any]]:
        """Decode CAN ID 0x650: Lights/LED Status"""
        # D0 bit 0 -- low beam on
        low_beam = (msg.data[0] & 0b00000001) == 1
        yield msg.id, "low_beam_on", low_beam

        # D0 bit 1 -- high beam on
        high_beam = ((msg.data[0] & 0b00000010) >> 1) == 1
        yield msg.id, "high_beam_on", high_beam

        # D0 bit 2 -- brake light on
        brake_light = ((msg.data[0] & 0b00000100) >> 2) == 1
        yield msg.id, "brake_light_on", brake_light

        # D0 bit 3 -- turn signal left on
        turn_left = ((msg.data[0] & 0b00001000) >> 3) == 1
        yield msg.id, "turn_signal_left", turn_left

        # D0 bit 4 -- turn signal right on
        turn_right = ((msg.data[0] & 0b00010000) >> 4) == 1
        yield msg.id, "turn_signal_right", turn_right
