import argparse
import json
import pytz

import pandas as pd

from datetime import datetime, time, timedelta, timezone
from decimal import Decimal
from enum import Enum
from functools import total_ordering


ZRH = pytz.timezone('Europe/Zurich')


def is_timezone_naive(d: time | datetime) -> bool:
    return d.tzinfo is None or d.tzinfo.utcoffset(d) is None


@total_ordering
class EnergyRate(Enum):
    LOW = 1
    HIGH = 2

    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.value < other.value
        return NotImplemented


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


    class Key(str, Enum):
        ENERGY = 'Energy'
        TIMESTAMP = 'Timestamp'


    def __init__(self, energy_detail: dict):
        got_keys = sorted(energy_detail.keys())
        want_keys = sorted([k.value for k in EnergyDetail.Key])
        assert want_keys == got_keys,\
            'Unexpected EnergyDetail keys: want %s, got %s.' % (want_keys, got_keys)

        energy = energy_detail[EnergyDetail.Key.ENERGY]
        timestamp = datetime.fromisoformat(energy_detail[EnergyDetail.Key.TIMESTAMP])

        assert energy >= 0,\
            'The energy is < 0 for energy detail: %s.' % (energy_detail,)
        assert timestamp.tzinfo == timezone.utc,\
            'The timestamp is not in UTC for energy detail: %s.' % (energy_detail,)

        self.energy = energy
        self.timestamp = timestamp.astimezone(ZRH)


    def compute_energy_rate(self, weekday_to_optional_high_rate_interval: [HighRateInterval | None]) -> EnergyRate:
        earliest_timestamp = self.timestamp - EnergyDetail.TIMESTAMP_RECORD_DELAY
        optional_high_rate_interval = weekday_to_optional_high_rate_interval[earliest_timestamp.weekday()]

        if optional_high_rate_interval is None:
            return EnergyRate.LOW
        return EnergyRate.HIGH if optional_high_rate_interval.includes(earliest_timestamp.time()) else EnergyRate.LOW


class ChargeSession:
    class Key(str, Enum):
        DEVICE_ID = 'DeviceId'
        DEVICE_NAME = 'DeviceName'
        ENERGY = 'Energy'
        ENERGY_DETAILS = 'EnergyDetails'
        END_DATE_TIME = 'EndDateTime'
        START_DATE_TIME = 'StartDateTime'


    def __init__(self, charge_session: dict):
        for k in ChargeSession.Key:
            if k.value == ChargeSession.Key.ENERGY_DETAILS:
                continue  # This key is optional.
            assert k.value in charge_session, 'Missing charge session key: %s.' % (k.value,)

        energy = charge_session[ChargeSession.Key.ENERGY]
        end_date_time = datetime.fromisoformat(charge_session[ChargeSession.Key.END_DATE_TIME])
        start_date_time = datetime.fromisoformat(charge_session[ChargeSession.Key.START_DATE_TIME])

        assert energy >= 0,\
            'The energy is < 0 for charge session: %s.' % (charge_session,)
        assert is_timezone_naive(end_date_time,),\
            'Unexpected timezone for end datetime (%s) of charge session %s' % (end_date_time, charge_session,)
        assert is_timezone_naive(start_date_time,),\
            'Unexpected timezone for start datetime of charge session %s' % (start_date_time, charge_session,)

        self.optional_energy_details = charge_session.get(ChargeSession.Key.ENERGY_DETAILS)

        self.device_id = charge_session[ChargeSession.Key.DEVICE_ID]
        self.device_name = charge_session[ChargeSession.Key.DEVICE_NAME]
        self.energy = energy
        self.end_date_time = pytz.utc.localize(end_date_time).astimezone(ZRH)
        self.start_date_time = pytz.utc.localize(start_date_time).astimezone(ZRH)


    def get_energy_details(self) -> [EnergyDetail]:
        assert self.optional_energy_details is not None,\
            'Unimplemented'

        return [EnergyDetail(ed) for ed in self.optional_energy_details]


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

    @total_ordering
    class TableColumns(str, Enum):
        DEVICE_ID = 'DeviceId'
        DEVICE_NAME = 'DeviceName'
        TIMESTAMP = 'Timestamp'
        ENERGY = 'Energy'
        ENERGY_RATE = 'EnergyRate'

        def __lt__(self, other):
            if self.__class__ is other.__class__:
                return self.value < other.value
            return NotImplemented

    energy_details_rows = []
    for charge_session_json in chargehistory_json['Data']:
        charge_session = ChargeSession(charge_session_json)

        for energy_detail in charge_session.get_energy_details():
            energy_details_rows.append([
                charge_session.device_id,
                charge_session.device_name,
                energy_detail.timestamp,
                energy_detail.energy,
                energy_detail.compute_energy_rate(WEEKDAY_TO_OPTIONAL_HIGH_RATE_INTERVAL)])

    energy_details_df = pd.DataFrame(
        energy_details_rows, columns=[k for k in TableColumns])
    summary_df = pd.pivot_table(
        energy_details_df[[
            TableColumns.DEVICE_ID,
            TableColumns.DEVICE_NAME,
            TableColumns.ENERGY,
            TableColumns.ENERGY_RATE]],
        values=TableColumns.ENERGY,
        index=[TableColumns.DEVICE_ID, TableColumns.DEVICE_NAME],
        columns=[TableColumns.ENERGY_RATE],
        aggfunc=sum)

    print(summary_df)


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
