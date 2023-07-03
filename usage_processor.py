import argparse
import json
import pytz

from datetime import datetime, time, timedelta, timezone
from decimal import Decimal
from enum import Enum
from pprint import pprint


ZRH = pytz.timezone('Europe/Zurich')


class EnergyRate(Enum):
    LOW = 1
    HIGH = 2


class EnergyDetailKey(str, Enum):
    ENERGY = 'Energy'
    TIMESTAMP = 'Timestamp'


def is_timezone_naive(d: time | datetime) -> bool:
    return d.tzinfo is None or d.tzinfo.utcoffset(d) is None


class HighRateInterval:
    def __init__(self, start: time, end: time):
        assert is_timezone_naive(start),\
            'the start of the high rate interval should not have time zone info, but it has: %s.' % (start.tzinfo,)
        assert is_timezone_naive(end),\
            'the end of the high rate interval should not have time zone info, but it has: %s.' % (end.tzinfo,)
        assert start < end,\
            'the high rate interval needs to start before it ends, but %s is not before %s.' % (start, end)

        self.start = start
        self.end = end


    def includes(self, t: time):
        return self.start < t and t <= self.end


class EnergyDetail:
    # The energy detail recording delay.
    TIMESTAMP_RECORD_DELAY = timedelta(seconds=1)

    def __init__(self, energy_detail: dict):
        got_keys = sorted(energy_detail.keys())
        want_keys = sorted([k.value for k in EnergyDetailKey])
        assert want_keys == got_keys,\
            'Unexpected EnergyDetail keys: want %s, got %s.' % (want_keys, got_keys)

        energy = energy_detail[EnergyDetailKey.ENERGY]
        timestamp = datetime.fromisoformat(energy_detail[EnergyDetailKey.TIMESTAMP])

        assert energy >= 0,\
            'The energy is not >= for energy detail: %s.' % (energy_detail,)
        assert timestamp.tzinfo == timezone.utc,\
            'The timestamp is not in UTC for energy detail: %s.' % (energy_detail,)

        self.energy = energy
        self.timestamp = timestamp.astimezone(ZRH)


    def rate(self, weekday_to_optional_high_rate_interval: [HighRateInterval | None]) -> EnergyRate:
        earliest_timestamp = self.timestamp - EnergyDetail.TIMESTAMP_RECORD_DELAY
        optional_high_rate_interval = weekday_to_optional_high_rate_interval[earliest_timestamp.weekday()]

        if optional_high_rate_interval is None:
            return EnergyRate.LOW
        return EnergyRate.HIGH if optional_high_rate_interval.includes(earliest_timestamp.time()) else EnergyRate.LOW


def process_usage(
        chargehistory_file_path: str,
        weekday_high_rate_interval: HighRateInterval = None,
        saturday_high_rate_interval: HighRateInterval = None):

    # The high-rate interval for a date or datetime .weekday().
    WEEKDAY_TO_OPTIONAL_HIGH_RATE_INTERVAL = [
        weekday_high_rate_interval,   # Monday
        weekday_high_rate_interval,   # Tuesday
        weekday_high_rate_interval,   # Wednesday
        weekday_high_rate_interval,   # Thursday
        weekday_high_rate_interval,   # Friday
        saturday_high_rate_interval,  # Saturday
        None,                         # Sunday
    ]

    with open(chargehistory_file_path) as chargehistory_file:
        chargehistory_json = json.load(chargehistory_file, parse_float=Decimal)

    for energy_detail in chargehistory_json['Data'][-1]['EnergyDetails']:
        pprint(energy_detail)
        print(EnergyDetail(energy_detail).rate(WEEKDAY_TO_OPTIONAL_HIGH_RATE_INTERVAL))
        print()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Process usage fetched from \'https://api.zaptec.com/api/chargehistory/\'.')

    parser.add_argument(
        'chargehistory_file_path',
        help='the path to the Zaptec chargehistory API response, in JSON format')
    parser.add_argument(
        '--weekday_high_rate_interval',
        nargs=2,
        type=time.fromisoformat,
        help='the high-rate weekdays interval, in the Europe/Zurich time zone, but without explicit time zone info')
    parser.add_argument(
        '--saturday_high_rate_interval',
        nargs=2,
        type=time.fromisoformat,
        help='the high-rate Saturday interval, in the Europe/Zurich time zone, but without explicit time zone info')

    args = parser.parse_args()

    process_usage(
        chargehistory_file_path=args.chargehistory_file_path,
        weekday_high_rate_interval=
            HighRateInterval(args.weekday_high_rate_interval[0], args.weekday_high_rate_interval[1])
            if args.weekday_high_rate_interval is not None
            else None,
        saturday_high_rate_interval=
            HighRateInterval(args.saturday_high_rate_interval[0], args.saturday_high_rate_interval[1])
            if args.saturday_high_rate_interval is not None
            else None)
