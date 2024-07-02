import pytz

from datetime import datetime, time


ZRH = pytz.timezone('Europe/Zurich')


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
