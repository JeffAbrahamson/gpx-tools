from datetime import datetime

from fitmap.fit import SEMICIRCLES_TO_DEGREES, parse_record_message


class Message:
    def __init__(self, values):
        self.values = values

    def get_value(self, name):
        value = self.values.get(name)
        if value is None:
            raise KeyError(name)
        return value


def test_parse_record_message_converts_semicircles():
    message = Message(
        {
            "timestamp": datetime(2026, 5, 1, 12, 0),
            "position_lat": int(47.0 / SEMICIRCLES_TO_DEGREES),
            "position_long": int(7.0 / SEMICIRCLES_TO_DEGREES),
            "enhanced_altitude": 500.5,
            "heart_rate": 135,
            "cadence": 82,
            "power": 210,
            "enhanced_speed": 8.5,
            "distance": 1234.5,
        }
    )

    point = parse_record_message(message)

    assert point is not None
    assert round(point.latitude, 4) == 47.0
    assert round(point.longitude, 4) == 7.0
    assert point.elevation == 500.5
    assert point.heart_rate == 135
    assert point.cadence == 82
    assert point.power == 210
    assert point.speed == 8.5
    assert point.distance == 1234.5


def test_parse_record_message_skips_record_without_gps():
    assert parse_record_message(Message({"timestamp": datetime(2026, 5, 1)})) is None
