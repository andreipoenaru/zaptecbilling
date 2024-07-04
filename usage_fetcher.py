import argparse
import inquirer
import json
import os
import pytz
import requests

from datetime import datetime, timedelta
from enum import Enum
from getpass import getpass
from http import HTTPStatus
from ratelimit import limits, sleep_and_retry

from common import ChargeSession, UsageInterval, ZRH


DATA_KEY = 'Data'


def fetch_access_token(
        username: str,
        password: str) -> str:
    AUTH_URL = 'https://api.zaptec.com/oauth/token'
    ACCESS_TOKEN_KEY = 'access_token'

    data = {
        'grant_type': 'password',
        'username': username,
        'password': password,
    }

    response = requests.post(AUTH_URL, data=data)
    assert response.status_code == HTTPStatus.OK,\
        'expected auth respose status code to be 200 (OK), but it was: %d.' % (response.status_code,)

    response_json = response.json()
    assert ACCESS_TOKEN_KEY in response_json,\
        'access token not in auth response json: %s.' % (response_json,)

    return response_json[ACCESS_TOKEN_KEY]


class DetailLevel(Enum):
    SUMMARY = 0
    DETAILED = 1


@sleep_and_retry
@limits(calls=900, period=60)
def fetch_chargehistory_page(
        access_token: str,
        installation_id: str,
        fetch_interval: UsageInterval,
        page_size: int = 5000,
        page_index: int = 0,
        detail_level: int = DetailLevel.SUMMARY,
        include_disabled: bool = True) -> dict:
    CHARGEHISTORY_URL = 'https://api.zaptec.com/api/chargehistory'
    AUTH_KEY = 'Authorization'
    INSTALLATION_ID_KEY = 'InstallationId'
    FROM_KEY = 'From'
    TO_KEY = 'To'
    PAGE_SIZE_KEY = 'PageSize'
    PAGE_INDEX_KEY = 'PageIndex'
    DETAIL_LEVEL_KEY = 'DetailLevel'
    INCLUDE_DISABLED_KEY = 'IncludeDisabled'

    headers = {
        AUTH_KEY: 'Bearer %s' % (access_token,),
    }
    params = {
        INSTALLATION_ID_KEY: installation_id,
        FROM_KEY: fetch_interval.start_date_time.astimezone(pytz.utc).isoformat(),
        TO_KEY: fetch_interval.end_date_time.astimezone(pytz.utc).isoformat(),
        PAGE_SIZE_KEY: page_size,
        PAGE_INDEX_KEY: page_index,
        DETAIL_LEVEL_KEY: detail_level.value,
        INCLUDE_DISABLED_KEY: include_disabled,
    }

    response = requests.get(CHARGEHISTORY_URL, headers=headers, params=params)
    assert response.status_code == HTTPStatus.OK,\
        'expected chargehistory respose status code to be 200 (OK), but it was: %d.' % (response.status_code,)

    return response.json()


def fetch_chargehistory(
        access_token: str,
        installation_id: str,
        fetch_interval: UsageInterval,
        detail_level: int = DetailLevel.SUMMARY,
        include_disabled: bool = True) -> dict:
    PAGES_KEY = 'Pages'

    response_json = fetch_chargehistory_page(
        access_token=access_token,
        installation_id=installation_id,
        fetch_interval=fetch_interval,
        detail_level=detail_level,
        include_disabled=include_disabled)
    assert PAGES_KEY in response_json, 'missing \'%s\' from response json: %s.' % (PAGES_KEY, response_json)
    assert response_json[PAGES_KEY] >= 0, 'the number of pages is < 0: %s.' % (response_json,)
    assert DATA_KEY in response_json, 'missing \'%s\' from response json: %s.' % (DATA_KEY, response_json)

    for page_index in range(1, response_json[PAGES_KEY]):
        page_json = fetch_chargehistory_page(
            access_token=access_token,
            installation_id=installation_id,
            fetch_interval=fetch_interval,
            page_index=page_index,
            detail_level=detail_level,
            include_disabled=include_disabled)
        assert DATA_KEY in page_json, 'missing \'%s\' from page json: %s.' % (DATA_KEY, page_json)

        response_json[DATA_KEY].extend(page_json[DATA_KEY])

    return response_json


def determine_fetch_interval(
        access_token: str,
        installation_id: str,
        usage_interval: UsageInterval,
        num_charging_stations: int) -> UsageInterval:
    current_date_time = datetime.now(ZRH)
    assert usage_interval.end_date_time <= current_date_time,\
        'the usage interval ends in the future'

    FETCH_INCREMENT_TIMEDELTA = min(timedelta(weeks=1), current_date_time - usage_interval.end_date_time)
    MAX_TOTAL_ADDED_TIMEDELTA = min(timedelta(weeks=4), current_date_time - usage_interval.end_date_time)

    fetch_interval = usage_interval.copy()
    fetch_interval_step = usage_interval.copy()
    device_id_set = set()

    while len(device_id_set) < num_charging_stations and\
            fetch_interval.end_date_time + FETCH_INCREMENT_TIMEDELTA\
            <= usage_interval.end_date_time + MAX_TOTAL_ADDED_TIMEDELTA:
        fetch_interval.end_date_time += FETCH_INCREMENT_TIMEDELTA

        fetch_interval_step.start_date_time = fetch_interval_step.end_date_time
        fetch_interval_step.end_date_time += FETCH_INCREMENT_TIMEDELTA

        chargehistory_json = fetch_chargehistory(
            access_token=access_token,
            installation_id=installation_id,
            fetch_interval=fetch_interval_step)

        for charge_session_json in chargehistory_json[DATA_KEY]:
            charge_session = ChargeSession(charge_session_json)

            if usage_interval.end_date_time <= charge_session.end_date_time:
                device_id_set.add(charge_session.device_id)

    assert len(device_id_set) >= num_charging_stations,\
        'didn\'t manage to find a charging session after the usage interval for all charging stations: %s' % (device_id_set,)
    return fetch_interval


def fetch_usage(
        username: str,
        password: str,
        installation_id: str,
        usage_interval: UsageInterval,
        num_charging_stations: int,
        output_chargehistory_file_name: str) -> None:
    assert num_charging_stations > 0,\
        'the number of charging stations needs to be > 0, but it was: %d.' % (num_charging_stations,)

    access_token = fetch_access_token(
        username=username,
        password=password)

    fetch_interval = determine_fetch_interval(
        access_token=access_token,
        installation_id=installation_id,
        usage_interval=usage_interval,
        num_charging_stations=num_charging_stations)
    print('Fetching charging history for the interval: %s - %s'
        % (fetch_interval.start_date_time, fetch_interval.end_date_time))

    chargehistory_json = fetch_chargehistory(
        access_token=access_token,
        installation_id=installation_id,
        fetch_interval=fetch_interval,
        detail_level=DetailLevel.DETAILED)

    if os.path.exists(output_chargehistory_file_name):
        answers = inquirer.prompt([
            inquirer.List(
                'overwrite_file',
                message='Overwrite file?',
                choices=['Yes', 'No'],
                default='No')])
        if answers['overwrite_file'] != 'Yes':
            print('Data not saved.')
            return

    with open(output_chargehistory_file_name, 'w') as chargehistory_file:
        json.dump(chargehistory_json, chargehistory_file, indent=2)


def main():
    parser = argparse.ArgumentParser(
        description='Fetch usage data from \'https://api.zaptec.com/api/chargehistory/\'.')

    parser.add_argument(
        'username',
        help='the Zaptec account username, for calling the Zaptec API; '
        'the password will be prompted during execution')
    parser.add_argument(
        'installation_id',
        help='the Zaptec installation ID')
    parser.add_argument(
        'usage_interval_start',
        type=datetime.fromisoformat,
        help='the start of the usage reporting period, in the Europe/Zurich time zone, '
        'but without explicit time zone info')
    parser.add_argument(
        'usage_interval_end',
        type=datetime.fromisoformat,
        help='the end of the usage reporting period, in the Europe/Zurich time zone, '
        'but without explicit time zone info')
    parser.add_argument(
        'num_charging_stations',
        type=int,
        help='the number of charging stations for which to include at least one session that ended '
        'after the usage period')
    parser.add_argument(
        'output_chargehistory_file_name',
        help='the path to the output Zaptec chargehistory API response, in JSON format')

    args = parser.parse_args()
    password = getpass()

    fetch_usage(
        username=args.username,
        password=password,
        installation_id=args.installation_id,
        usage_interval=UsageInterval(args.usage_interval_start, args.usage_interval_end),
        num_charging_stations=args.num_charging_stations,
        output_chargehistory_file_name=args.output_chargehistory_file_name)


if __name__ == '__main__':
    main()
