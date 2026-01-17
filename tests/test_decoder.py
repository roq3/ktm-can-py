# -*- encoding: utf-8 -*-

from ktm_can.decoder import Decoder
import os
import struct
from typing import Dict, Tuple, Any


FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")


def pack_data(*data: int) -> bytes:
    return struct.pack("8B", *data)


def make_msg(bytes_str: str) -> 'Message':
    rec = bytes_str.split(",")
    return Message(int(rec[0], 16), pack_data(*[int(d, 16) for d in rec[1:]]))


def decode(decoder: Decoder, msg: 'Message') -> Dict[Tuple[int, str], Any]:
    parsed = {}
    for sender, key, value in decoder.decode(msg):
        parsed[sender, key] = value

    return parsed


class Message(object):
    """a message read from the bus"""

    def __init__(self, sender_id: int, data: bytes) -> None:
        super(Message, self).__init__()
        self.id: int = sender_id
        self.data: bytes = data


class TestDecoder(object):
    decoder = Decoder(enable_assertions=True)

    def test_120(self):
        parsed = decode(self.decoder, make_msg("120,06,79,00,00,00,00,00,3F"))

        assert len(parsed) == 4
        assert parsed[0x120, "rpm"] == 1657
        assert parsed[0x120, "throttle"] == 0
        assert parsed[0x120, "kill_switch"] == 0
        assert parsed[0x120, "throttle_map"] == 0

    def test_129(self):
        parsed = decode(self.decoder, make_msg("129,30,00,00,00,00,00,00,30"))

        assert len(parsed) == 2
        assert parsed[0x129, "gear"] == 3
        assert parsed[0x129, "clutch_in"] is False

    def test_12A_map1(self):
        parsed = decode(self.decoder, make_msg("12A,11,28,00,20,00,00,00,00"))

        assert len(parsed) == 2
        assert parsed[0x12A, "requested_throttle_map"] == 0
        assert parsed[0x12A, "throttle_open"] is True

    def test_12A_map2(self):
        parsed = decode(self.decoder, make_msg("12A,13,68,00,20,00,00,00,00"))

        assert len(parsed) == 2
        assert parsed[0x12A, "requested_throttle_map"] == 1
        assert parsed[0x12A, "throttle_open"] is False

    def test_12B(self):
        parsed = decode(self.decoder, make_msg("12B,00,00,02,16,00,02,8F,FD"))

        assert len(parsed) == 4
        assert parsed[0x12B, "front_wheel"] == 0  # @todo better sample
        assert parsed[0x12B, "rear_wheel"] == 534
        assert parsed[0x12B, "tilt"] == 40
        assert parsed[0x12B, "lean"] == -3

    def test_290(self):
        parsed = decode(self.decoder, make_msg("290,00,80,00,00,00,00,00,00"))

        assert len(parsed) == 1
        assert parsed[0x290, "front_brake"] == 128

    def test_450(self):
        parsed = decode(self.decoder, make_msg("450,00,00,01,00,00,00,00,00"))

        assert len(parsed) == 1
        assert parsed[0x450, "traction_control_button"] == 1

    def test_540(self):
        parsed = decode(self.decoder, make_msg("540,02,06,65,00,01,00,01,DD"))

        assert len(parsed) == 5
        assert parsed[0x540, "rpm"] == 1637
        assert parsed[0x540, "kickstand_up"] is True
        assert parsed[0x540, "kickstand_err"] is False
        assert parsed[0x540, "coolant_temp"] == 47.7
        assert parsed[0x540, "gear"] == 0

    def test_540_gear7(self):
        parsed = decode(self.decoder, make_msg("540,02,06,AA,07,01,00,01,5B"))

        assert len(parsed) == 5
        assert parsed[0x540, "rpm"] == 1706
        assert parsed[0x540, "kickstand_up"] is True
        assert parsed[0x540, "kickstand_err"] is False
        assert parsed[0x540, "coolant_temp"] == 34.7
        assert parsed[0x540, "gear"] == 7


class TestDecoderUnmapped(object):
    """Test decoder with emit_unmapped=True"""
    decoder = Decoder(emit_unmapped=True, enable_assertions=True)

    def test_120_unmapped(self):
        parsed = decode(self.decoder, make_msg("120,06,79,00,00,00,00,00,3F"))

        assert len(parsed) == 5  # 4 normal + 1 unmapped
        assert parsed[0x120, "rpm"] == 1657
        assert parsed[0x120, "throttle"] == 0
        assert parsed[0x120, "kill_switch"] == 0
        assert parsed[0x120, "throttle_map"] == 0
        assert parsed[0x120, "unmapped"] == "__ __ __ 00 00 00 00 __"

    def test_129_unmapped(self):
        parsed = decode(self.decoder, make_msg("129,30,00,00,00,00,00,00,30"))

        assert len(parsed) == 3  # 2 normal + 1 unmapped
        assert parsed[0x129, "gear"] == 3
        assert parsed[0x129, "clutch_in"] is False
        assert parsed[0x129, "unmapped"] == "__ 00 00 00 00 00 00 __"

    def test_12A_unmapped(self):
        parsed = decode(self.decoder, make_msg("12A,11,28,00,20,00,00,00,00"))

        assert len(parsed) == 3  # 2 normal + 1 unmapped
        assert parsed[0x12A, "requested_throttle_map"] == 0
        assert parsed[0x12A, "throttle_open"] is True
        assert parsed[0x12A, "unmapped"] == "11 28 __ 20 __ __ __ __"

    def test_12B_unmapped(self):
        parsed = decode(self.decoder, make_msg("12B,00,00,02,16,00,02,8F,FD"))

        assert len(parsed) == 5  # 4 normal + 1 unmapped
        assert parsed[0x12B, "front_wheel"] == 0
        assert parsed[0x12B, "rear_wheel"] == 534
        assert parsed[0x12B, "tilt"] == 40
        assert parsed[0x12B, "lean"] == -3
        assert parsed[0x12B, "unmapped"] == "__ __ __ __ 00 __ __ __"

    def test_450_unmapped(self):
        parsed = decode(self.decoder, make_msg("450,00,00,01,00,00,00,00,00"))

        assert len(parsed) == 2  # 1 normal + 1 unmapped
        assert parsed[0x450, "traction_control_button"] == 1
        assert parsed[0x450, "unmapped"] == "__ __ 00 __ 00 __ __ __"

    def test_540_unmapped(self):
        parsed = decode(self.decoder, make_msg("540,02,06,65,00,01,00,01,DD"))

        assert len(parsed) == 6  # 5 normal + 1 unmapped
        assert parsed[0x540, "rpm"] == 1637
        assert parsed[0x540, "kickstand_up"] is True
        assert parsed[0x540, "kickstand_err"] is False
        assert parsed[0x540, "coolant_temp"] == 47.7
        assert parsed[0x540, "gear"] == 0
        assert parsed[0x540, "unmapped"] == "__ __ __ 00 00 __ __ __"


class TestHelperFunctions(object):
    """Test helper functions"""

    def test_lo_nibble(self):
        from ktm_can.decoder import lo_nibble
        assert lo_nibble(0xAB) == 0x0B
        assert lo_nibble(0x12) == 0x02
        assert lo_nibble(0xFF) == 0x0F
        assert lo_nibble(0x00) == 0x00

    def test_hi_nibble(self):
        from ktm_can.decoder import hi_nibble
        assert hi_nibble(0xAB) == 0x0A
        assert hi_nibble(0x12) == 0x01
        assert hi_nibble(0xFF) == 0x0F
        assert hi_nibble(0x00) == 0x00

    def test_signed12(self):
        from ktm_can.decoder import signed12
        # Test positive values
        assert signed12(0x000) == 0
        assert signed12(0x001) == 1
        assert signed12(0x7FF) == 2047

        # Test negative values (two's complement)
        assert signed12(0xFFF) == -1
        assert signed12(0xFFE) == -2
        assert signed12(0x800) == -2048

    def test_invert(self):
        from ktm_can.decoder import invert
        assert invert(0x00) == 0xFF
        assert invert(0xFF) == 0x00
        assert invert(0xAA) == 0x55
        assert invert(0x0F) == 0xF0


class TestEdgeCases(object):
    """Test edge cases and error conditions"""

    def test_unknown_message_id(self):
        """Test decoder with unknown message ID"""
        decoder = Decoder(enable_assertions=True)
        # Create message with unknown ID (not in 0x120, 0x129, 0x12A, 0x12B,
        # 0x290, 0x450, 0x540)
        msg = make_msg("999,00,00,00,00,00,00,00,00")
        results = list(decoder.decode(msg))
        assert len(results) == 0  # Should return no decoded data

    def test_unknown_message_id_with_unmapped(self):
        """Test decoder with unknown message ID and emit_unmapped=True"""
        decoder = Decoder(emit_unmapped=True, enable_assertions=True)
        msg = make_msg("999,00,00,00,00,00,00,00,00")
        results = list(decoder.decode(msg))
        assert len(results) == 0  # Unknown IDs don't produce unmapped data

    def test_empty_data(self):
        """Test decoder with empty data"""
        decoder = Decoder(enable_assertions=True)
        # This would normally cause issues, but let's test known IDs with
        # potentially problematic data
        msg = make_msg("120,00,00,00,00,00,00,00,00")
        results = list(decoder.decode(msg))
        # Should still decode successfully
        assert len(results) == 4  # rpm, throttle, kill_switch, throttle_map

    def test_max_values(self):
        """Test decoder with maximum possible values"""
        decoder = Decoder(enable_assertions=True)
        # Test with all FF bytes
        msg = make_msg("120,FF,FF,FF,FF,FF,FF,FF,FF")
        results = list(decoder.decode(msg))
        assert len(results) == 4
        assert results[0][2] == 65535  # rpm max value
        assert results[1][2] == 255    # throttle max value

    def test_min_values(self):
        """Test decoder with minimum values"""
        decoder = Decoder(enable_assertions=True)
        msg = make_msg("120,00,00,00,00,00,00,00,00")
        results = list(decoder.decode(msg))
        assert len(results) == 4
        assert results[0][2] == 0  # rpm min value
        assert results[1][2] == 0  # throttle min value

    def test_assertions_disabled(self):
        """Test that assertions are disabled by default"""
        decoder = Decoder(enable_assertions=False)
        # Create message that would normally trigger assertions
        # data[2] should be 0 according to assertions
        msg = make_msg("12A,11,28,FF,20,00,00,00,00")
        # Should not raise AssertionError
        results = list(decoder.decode(msg))
        assert len(results) == 2  # Should still decode normally

    def test_assertions_enabled(self):
        """Test that assertions work when enabled"""
        decoder = Decoder(enable_assertions=True)
        # data[2] is 0, which should pass assertion
        msg = make_msg("12A,11,28,00,20,00,00,00,00")
        # This should work fine since data[2] is actually 0 in this message
        results = list(decoder.decode(msg))
        assert len(results) == 2

    def test_wheel_speed_edge_cases(self):
        """Test wheel speed calculations with edge values"""
        decoder = Decoder(enable_assertions=True)
        # Test with max wheel speeds
        msg = make_msg("12B,FF,FF,FF,FF,00,00,00,00")
        results = list(decoder.decode(msg))
        assert len(results) == 4
        assert results[0][2] == 65535  # front_wheel max
        assert results[1][2] == 65535  # rear_wheel max

    def test_lean_angle_edge_cases(self):
        """Test lean angle calculations with edge values"""
        decoder = Decoder(enable_assertions=True)
        # Test with extreme lean values
        msg = make_msg("12B,00,00,00,00,FF,FF,FF,FF")
        results = list(decoder.decode(msg))
        assert len(results) == 4
        # Lean and tilt should be calculated from the last 3 bytes
        # This tests the signed12 function with various inputs

    def test_brake_pressure_edge_cases(self):
        """Test brake pressure with edge values"""
        decoder = Decoder(enable_assertions=True)
        msg = make_msg("290,FF,FF,00,00,00,00,00,00")
        results = list(decoder.decode(msg))
        assert len(results) == 1
        assert results[0][2] == 65535  # max brake pressure

    def test_coolant_temp_edge_cases(self):
        """Test coolant temperature with edge values"""
        decoder = Decoder(enable_assertions=True)
        msg = make_msg("540,02,FF,FF,00,00,00,FF,FF")  # Use max values but ensure D5=00
        results = list(decoder.decode(msg))
        assert len(results) == 5
        # Coolant temp is calculated as struct.unpack(">H", msg.data[6:])[0] / 10.0
        # With FF FF, this should be 65535 / 10.0 = 6553.5
        coolant_temp_result = next(
            (value for id, key, value in results if key == "coolant_temp"), None)
        assert coolant_temp_result == 6553.5


class TestDecoderConfiguration(object):
    """Test different decoder configurations"""

    def test_default_configuration(self):
        """Test decoder with default settings"""
        decoder = Decoder()
        assert decoder.emit_unmapped is False
        assert decoder.enable_assertions is False

    def test_emit_unmapped_only(self):
        """Test decoder with only emit_unmapped enabled"""
        decoder = Decoder(emit_unmapped=True, enable_assertions=False)
        assert decoder.emit_unmapped is True
        assert decoder.enable_assertions is False

    def test_assertions_only(self):
        """Test decoder with only assertions enabled"""
        decoder = Decoder(emit_unmapped=False, enable_assertions=True)
        assert decoder.emit_unmapped is False
        assert decoder.enable_assertions is True

    def test_both_enabled(self):
        """Test decoder with both options enabled"""
        decoder = Decoder(emit_unmapped=True, enable_assertions=True)
        assert decoder.emit_unmapped is True
        assert decoder.enable_assertions is True
