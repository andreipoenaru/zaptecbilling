import inquirer
import pprint
import pytz

from datetime import datetime, time, timedelta, timezone
from enum import Enum
from functools import total_ordering


ZRH = pytz.timezone('Europe/Zurich')
TIMESTAMP_RECORD_DELAY = timedelta(seconds=5)


def is_timezone_naive(d: time | datetime) -> bool:
    return d.tzinfo is None or d.tzinfo.utcoffset(d) is None


class UsageInterval:
    def __init__(self, start_date_time: datetime, end_date_time: datetime):
        assert is_timezone_naive(start_date_time),\
            'the start of the usage reporting interval should not have time zone info, but it has: %s.' % (start_date_time.tzinfo,)
        assert is_timezone_naive(end_date_time),\
            'the end of the usage reporting interval should not have time zone info, but it has: %s.' % (end_date_time.tzinfo,)
        assert start_date_time < end_date_time,\
            'the usage reporting interval needs to start before it ends, but %s is not before %s.' % (start_date_time, end_date_time)

        self.start_date_time = ZRH.localize(start_date_time)
        self.end_date_time = ZRH.localize(end_date_time)


@total_ordering
class EnergyRate(str, Enum):
    LOW = 'LowEnergyRate'
    HIGH = 'HighEnergyRate'

    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.value < other.value
        return NotImplemented

    def get_text(self, locale: str):
            return ENERGY_RATE_LOCALES[locale][self]

ENERGY_RATE_LOCALES = {
    'de-CH': {
        EnergyRate.LOW: 'Niedertarif',
        EnergyRate.HIGH: 'Hochtarif',
    },
}


class HighRateInterval:
    def __init__(self, start_time: time, end_time: time):
        assert is_timezone_naive(start_time),\
            'the start of the high rate interval should not have time zone info, but it has: %s.' % (start_time.tzinfo,)
        assert is_timezone_naive(end_time),\
            'the end of the high rate interval should not have time zone info, but it has: %s.' % (end_time.tzinfo,)
        assert start_time < end_time,\
            'the high rate interval needs to start before it ends, but %s is not before %s.' % (start_time, end_time)

        self.start_time = start_time
        self.end_time = end_time


class EnergyDetail:
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
        earliest_timestamp = self.timestamp - TIMESTAMP_RECORD_DELAY
        optional_high_rate_interval = weekday_to_optional_high_rate_interval[earliest_timestamp.weekday()]

        if optional_high_rate_interval is None:
            return EnergyRate.LOW
        return EnergyRate.HIGH\
            if optional_high_rate_interval.start_time < earliest_timestamp.time()\
            and earliest_timestamp.time() <= optional_high_rate_interval.end_time\
            else EnergyRate.LOW


    def is_in_usage_interval(self, usage_interval: UsageInterval):
        earliest_timestamp = self.timestamp - TIMESTAMP_RECORD_DELAY
        return usage_interval.start_date_time < earliest_timestamp and earliest_timestamp <= usage_interval.end_date_time


class ChargeSession:
    class Key(str, Enum):
        COMMIT_END_DATE_TIME = 'CommitEndDateTime'
        DEVICE_ID = 'DeviceId'
        DEVICE_NAME = 'DeviceName'
        ENERGY = 'Energy'
        ENERGY_DETAILS = 'EnergyDetails'
        START_DATE_TIME = 'StartDateTime'


    def __init__(self, charge_session: dict):
        for k in ChargeSession.Key:
            if k.value == ChargeSession.Key.ENERGY_DETAILS:
                continue  # This key is optional.
            assert k.value in charge_session, 'Missing charge session key: %s.' % (k.value,)

        energy = charge_session[ChargeSession.Key.ENERGY]
        end_date_time = datetime.fromisoformat(charge_session[ChargeSession.Key.COMMIT_END_DATE_TIME])
        start_date_time = datetime.fromisoformat(charge_session[ChargeSession.Key.START_DATE_TIME])

        assert energy >= 0,\
            'The energy is < 0 for charge session: %s.' % (charge_session,)
        assert is_timezone_naive(end_date_time,),\
            'Unexpected timezone for end datetime (%s) of charge session %s' % (end_date_time, charge_session,)
        assert is_timezone_naive(start_date_time,),\
            'Unexpected timezone for start datetime of charge session %s' % (start_date_time, charge_session,)

        self.device_id = charge_session[ChargeSession.Key.DEVICE_ID]
        self.device_name = charge_session[ChargeSession.Key.DEVICE_NAME]
        self.energy = energy
        self.end_date_time = pytz.utc.localize(end_date_time).astimezone(ZRH)
        self.start_date_time = pytz.utc.localize(start_date_time).astimezone(ZRH)

        self.raw_charge_session = charge_session
        self.optional_energy_details = None
        self.optional_energy_rate = None
        self.comment = ''


    def compute_energy_details_or_rate(self, usage_interval: UsageInterval):
        optional_energy_details = [EnergyDetail(ed) for ed in self.raw_charge_session[ChargeSession.Key.ENERGY_DETAILS]]\
            if len(self.raw_charge_session.get(ChargeSession.Key.ENERGY_DETAILS, [])) > 0 else None
        optional_energy_rate = None
        comment = ''

        if optional_energy_details is None:
            assert usage_interval.start_date_time <= self.start_date_time\
                and self.end_date_time <= usage_interval.end_date_time,\
                'Charge sessions without energy details that don\'t fall entirely inside '\
                'the usage interval are not supported: %s' % (self.raw_charge_session,)

            print('The charging session that started on %s, %s and ended on %s, %s is missing energy details.' % (
                self.start_date_time.strftime('%A'),
                self.start_date_time,
                self.end_date_time.strftime('%A'),
                self.end_date_time))
            print('Here is the full json:')
            pprint.pprint(self.raw_charge_session)

            answers = inquirer.prompt([
                inquirer.List(
                    'energy_rate',
                    message='What energy rate did this charging session use?',
                    choices=[er.value for er in EnergyRate]),
                inquirer.Text(
                    'comment',
                    message='Add a comment about your selection:')])
            optional_energy_rate = EnergyRate(answers['energy_rate'])
            comment = answers['comment']

        self.optional_energy_details = optional_energy_details
        self.optional_energy_rate = optional_energy_rate
        self.comment = comment
