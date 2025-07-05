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

from common import is_timezone_naive, ChargeSession, UsageInterval, ZRH, TIMESTAMP_RECORD_DELAY


PAGES_KEY = 'Pages'
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
        'expected chargehistory response status code to be 200 (OK), but the response was:\n%s.'\
        % (json.dumps(response.json(), indent=2),)

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
        from_date_time: datetime,
        to_date_time: datetime | None = None,
        installation_id: str | None = None,
        charger_id: str | None = None,
        sort_property: str | None = None,
        sort_descending: bool | None = None,
        page_size: int = 100,
        page_index: int = 0,
        detail_level: int = DetailLevel.SUMMARY,
        include_disabled: bool = True) -> dict:
    CHARGEHISTORY_URL = 'https://api.zaptec.com/api/chargehistory'
    AUTH_KEY = 'Authorization'
    INSTALLATION_ID_KEY = 'InstallationId'
    FROM_KEY = 'From'
    CHARGER_ID_KEY = 'ChargerId'
    TO_KEY = 'To'
    SORT_PROPERTY_KEY = 'SortProperty'
    SORT_DESCENDING_KEY = 'SortDescending'
    PAGE_SIZE_KEY = 'PageSize'
    PAGE_INDEX_KEY = 'PageIndex'
    DETAIL_LEVEL_KEY = 'DetailLevel'
    INCLUDE_DISABLED_KEY = 'IncludeDisabled'

    headers = {
        AUTH_KEY: 'Bearer %s' % (access_token,),
    }
    params = {
        FROM_KEY: from_date_time.astimezone(pytz.utc).isoformat(),
        PAGE_SIZE_KEY: page_size,
        PAGE_INDEX_KEY: page_index,
        DETAIL_LEVEL_KEY: detail_level.value,
        INCLUDE_DISABLED_KEY: include_disabled,
    }
    if installation_id is not None:
        params[INSTALLATION_ID_KEY] = installation_id
    if charger_id is not None:
        params[CHARGER_ID_KEY] = charger_id
    if to_date_time is not None:
        params[TO_KEY] = to_date_time.astimezone(pytz.utc).isoformat()
    if sort_property is not None:
        params[SORT_PROPERTY_KEY] = sort_property
    if sort_descending is not None:
        params[SORT_DESCENDING_KEY] = sort_descending

    response = requests.get(CHARGEHISTORY_URL, headers=headers, params=params)
    assert response.status_code == HTTPStatus.OK,\
        'expected chargehistory response status code to be 200 (OK), but the response was:\n%s.'\
        % (json.dumps(response.json(), indent=2),)

    return response.json()


def fetch_chargehistory(
        access_token: str,
        installation_id: str,
        fetch_interval: UsageInterval,
        detail_level: int = DetailLevel.SUMMARY,
        include_disabled: bool = True) -> dict:
    response_json = fetch_chargehistory_page(
        access_token=access_token,
        from_date_time=fetch_interval.start_date_time,
        to_date_time=fetch_interval.end_date_time,
        installation_id=installation_id,
        detail_level=detail_level,
        include_disabled=include_disabled)
    assert PAGES_KEY in response_json, 'missing \'%s\' from response json: %s.' % (PAGES_KEY, response_json)
    assert response_json[PAGES_KEY] >= 0, 'the number of pages is < 0: %s.' % (response_json,)
    assert DATA_KEY in response_json, 'missing \'%s\' from response json: %s.' % (DATA_KEY, response_json)

    for page_index in range(1, response_json[PAGES_KEY]):
        page_json = fetch_chargehistory_page(
            access_token=access_token,
            from_date_time=fetch_interval.start_date_time,
            to_date_time=fetch_interval.end_date_time,
            installation_id=installation_id,
            page_index=page_index,
            detail_level=detail_level,
            include_disabled=include_disabled)
        assert DATA_KEY in page_json, 'missing \'%s\' from page json: %s.' % (DATA_KEY, page_json)

        response_json[DATA_KEY].extend(page_json[DATA_KEY])

    return response_json


@sleep_and_retry
@limits(calls=900, period=60)
def fetch_chargers_page(
        access_token: str,
        page_size: int = 100,
        page_index: int = 0,
        include_disabled: bool = True) -> dict:
    CHARGERS_URL = 'https://api.zaptec.com/api/chargers'
    AUTH_KEY = 'Authorization'
    PAGE_SIZE_KEY = 'PageSize'
    PAGE_INDEX_KEY = 'PageIndex'
    INCLUDE_DISABLED_KEY = 'IncludeDisabled'

    headers = {
        AUTH_KEY: 'Bearer %s' % (access_token,),
    }
    params = {
        PAGE_SIZE_KEY: page_size,
        PAGE_INDEX_KEY: page_index,
        INCLUDE_DISABLED_KEY: include_disabled,
    }

    response = requests.get(CHARGERS_URL, headers=headers, params=params)
    assert response.status_code == HTTPStatus.OK,\
        'expected chargehistory response status code to be 200 (OK), but the response was:\n%s.'\
        % (json.dumps(response.json(), indent=2),)

    return response.json()


def fetch_chargers(
        access_token: str,
        include_disabled: bool = True) -> dict:
    response_json = fetch_chargers_page(access_token=access_token)
    assert PAGES_KEY in response_json, 'missing \'%s\' from response json: %s.' % (PAGES_KEY, response_json)
    assert response_json[PAGES_KEY] >= 0, 'the number of pages is < 0: %s.' % (response_json,)
    assert DATA_KEY in response_json, 'missing \'%s\' from response json: %s.' % (DATA_KEY, response_json)

    for page_index in range(1, response_json[PAGES_KEY]):
        page_json = fetch_chargers_page(
            access_token=access_token,
            page_index=page_index)
        assert DATA_KEY in page_json, 'missing \'%s\' from page json: %s.' % (DATA_KEY, page_json)

        response_json[DATA_KEY].extend(page_json[DATA_KEY])

    return response_json


@sleep_and_retry
@limits(calls=900, period=60)
def fetch_charger_state(
        access_token: str,
        id: str) -> dict:
    CHARGER_STATE_URL = f'https://api.zaptec.com/api/chargers/{id}/state'
    AUTH_KEY = 'Authorization'

    headers = {
        AUTH_KEY: 'Bearer %s' % (access_token,),
    }

    response = requests.get(CHARGER_STATE_URL, headers=headers)
    assert response.status_code == HTTPStatus.OK,\
        'expected chargehistory response status code to be 200 (OK), but the response was:\n%s.'\
        % (json.dumps(response.json(), indent=2),)

    return response.json()


@sleep_and_retry
@limits(calls=900, period=60)
def fetch_constants(access_token: str) -> dict:
    CONSTANTS_URL = 'https://api.zaptec.com/api/constants'
    AUTH_KEY = 'Authorization'

    headers = {
        AUTH_KEY: 'Bearer %s' % (access_token,),
    }

    response = requests.get(CONSTANTS_URL, headers=headers)
    assert response.status_code == HTTPStatus.OK,\
        'expected chargehistory response status code to be 200 (OK), but the response was:\n%s.'\
        % (json.dumps(response.json(), indent=2),)

    return response.json()


@sleep_and_retry
@limits(calls=900, period=60)
def fetch_session_details(
        access_token: str,
        id: str) -> dict:
    SESSION_DETAILS_URL = f'https://api.zaptec.com/api/session/{id}'
    AUTH_KEY = 'Authorization'

    headers = {
        AUTH_KEY: 'Bearer %s' % (access_token,),
    }

    response = requests.get(SESSION_DETAILS_URL, headers=headers)
    assert response.status_code == HTTPStatus.OK,\
        'expected chargehistory response status code to be 200 (OK), but the response was:\n%s.'\
        % (json.dumps(response.json(), indent=2),)

    return response.json()


class Charger:
    class Key(str, Enum):
        ID = 'Id'
        DEVICE_ID = 'DeviceId'
        NAME = 'Name'
        INSTALLATION_ID = 'InstallationId'


    def __init__(self, charger: dict):
        for k in Charger.Key:
            assert k.value in charger, 'missing charger key: %s.' % (k.value,)

        self.id = charger[Charger.Key.ID]
        self.device_id = charger[Charger.Key.DEVICE_ID]
        self.name = charger[Charger.Key.NAME]
        self.installation_id = charger[Charger.Key.INSTALLATION_ID]


class Constants:
    def __init__(self, constants: dict):
        OBSERVATIONS = 'Observations'
        UNKNOWN = 'Unknown'
        PULSE = 'Pulse'
        SESSION_IDENTIFIER = 'SessionIdentifier'

        assert OBSERVATIONS in constants,\
            'missing \'%s\' in constants.' % (OBSERVATIONS,)
        assert UNKNOWN in constants[OBSERVATIONS],\
            'missing \'%s\' in observations.' %(UNKNOWN,)
        assert PULSE in constants[OBSERVATIONS],\
            'missing \'%s\' in observations.' %(PULSE,)
        assert SESSION_IDENTIFIER in constants[OBSERVATIONS],\
            'missing \'%s\' in observations.' %(SESSION_IDENTIFIER,)

        self.OBS_UNKNOWN = constants[OBSERVATIONS][UNKNOWN]
        self.OBS_PULSE = constants[OBSERVATIONS][PULSE]
        self.OBS_SESSION_IDENTIFIER = constants[OBSERVATIONS][SESSION_IDENTIFIER]


class ChargerState:
    class Key(str, Enum):
        CHARGER_ID = 'ChargerId'
        STATE_ID = 'StateId'
        TIMESTAMP = 'Timestamp'
        VALUE_AS_STRING = 'ValueAsString'


    @staticmethod
    def get_state_json(state_id: int, charger_state: list, CONSTANTS: Constants) -> dict | None:
        state_json_list = list(filter(
            lambda s: s.get(ChargerState.Key.STATE_ID, CONSTANTS.OBS_UNKNOWN) == state_id,
            charger_state))
        assert len(state_json_list) <= 1,\
            'more than one \'%d\' states for charger \'%s\''\
            % (state_id, state_json_list[0].get(ChargerState.Key.CHARGER_ID, '<unknown-charger-id>'))

        if len(state_json_list) < 1:
            return None

        state_json = state_json_list[0]
        assert ChargerState.Key.TIMESTAMP in state_json,\
            'missing timestamp in \'%d\' state of charger \'%s\''\
            % (state_id, state_json.get(ChargerState.Key.CHARGER_ID, '<unknown-charger-id>'))
        return state_json


    def __init__(self, charger_state: list, CONSTANTS: Constants):
        pulse_date_time = None
        pulse_json = ChargerState.get_state_json(CONSTANTS.OBS_PULSE, charger_state, CONSTANTS)
        if pulse_json is not None:
            pulse_date_time = datetime.fromisoformat(pulse_json[ChargerState.Key.TIMESTAMP])
            assert is_timezone_naive(pulse_date_time),\
                'the pulse timestamp should not have time zone info, but it has: %s.' % (pulse_date_time.tzinfo,)
            pulse_date_time = pytz.utc.localize(pulse_date_time).astimezone(ZRH)

        session_identifier_json = ChargerState.get_state_json(CONSTANTS.OBS_SESSION_IDENTIFIER, charger_state, CONSTANTS)
        session_identifier = None if session_identifier_json is None else session_identifier_json.get(ChargerState.Key.VALUE_AS_STRING, None)

        self.pulse_date_time = pulse_date_time
        self.session_identifier = session_identifier


class SessionDetails:
    class Key(str, Enum):
        SESSION_START = 'SessionStart'

    def __init__(self, session_details: dict):
        for k in SessionDetails.Key:
            assert k.value in session_details, 'missing session details key: %s.' % (k.value,)

        start_date_time = datetime.fromisoformat(session_details[SessionDetails.Key.SESSION_START])
        assert is_timezone_naive(start_date_time,),\
            'unexpected timezone for start datetime (%s) of session details %s.' % (start_date_time, session_details,)

        self.start_date_time = pytz.utc.localize(start_date_time).astimezone(ZRH)


def determine_fetch_interval(
        access_token: str,
        installation_id: str,
        usage_interval: UsageInterval) -> UsageInterval:
    current_date_time = datetime.now(ZRH)
    assert usage_interval.end_date_time <= current_date_time,\
        'the usage interval ends in the future'

    constants_json = fetch_constants(access_token)
    CONSTANTS = Constants(constants_json)

    fetch_interval = usage_interval.copy()
    chargers_json = fetch_chargers(access_token)
    for charger_json in chargers_json[DATA_KEY]:
        charger = Charger(charger_json)
        if charger.installation_id != installation_id:
            print('Charger \'%s\' (%s) is not part of the selected installation: skipping.'
                % (charger.name, charger.device_id))
            continue

        charger_state_json = fetch_charger_state(access_token, charger.id)
        charger_state = ChargerState(charger_state_json, CONSTANTS)

        assert charger_state.pulse_date_time is None\
                or usage_interval.end_date_time + TIMESTAMP_RECORD_DELAY <= charger_state.pulse_date_time,\
            'charger \'%s\' didn\'t send a pulse after the usage interval' % (charger.name,)

        if charger_state.session_identifier is not None:
            session_details_json = fetch_session_details(access_token, charger_state.session_identifier)
            session_details = SessionDetails(session_details_json)

            assert usage_interval.end_date_time + TIMESTAMP_RECORD_DELAY <= session_details.start_date_time,\
                'charger \'%s\' has an active session that started before the end of the usage interval.'\
                % (charger.name,)

        chargehistory_json = fetch_chargehistory_page(
                    access_token=access_token,
                    from_date_time=usage_interval.end_date_time + TIMESTAMP_RECORD_DELAY,
                    charger_id=charger.id,
                    sort_property='CommitEndDateTime',
                    sort_descending=True,
                    page_size=1)
        assert PAGES_KEY in chargehistory_json,\
            'missing \'%s\' from response json: %s.' % (PAGES_KEY, chargehistory_json)
        if chargehistory_json[PAGES_KEY] > 0:
            num_pages = chargehistory_json[PAGES_KEY]
            if num_pages > 1:
                chargehistory_json = fetch_chargehistory_page(
                        access_token=access_token,
                        from_date_time=usage_interval.end_date_time + TIMESTAMP_RECORD_DELAY,
                        charger_id=charger.id,
                        sort_property='CommitEndDateTime',
                        sort_descending=True,
                        page_size=1,
                        page_index=num_pages - 1)
                assert PAGES_KEY in chargehistory_json,\
                    'missing \'%s\' from response json: %s.' % (PAGES_KEY, chargehistory_json)

            assert chargehistory_json[PAGES_KEY] == num_pages,\
                'charger \'%s\' has finished a charging session while being processed: rerun the script.'\
                % (charger.name)
            assert DATA_KEY in chargehistory_json,\
                'missing \'%s\' from response json: %s.' % (DATA_KEY, chargehistory_json)
            assert len(chargehistory_json[DATA_KEY]) > 0,\
                'empty data in response json: %s.' % (chargehistory_json,)
            charge_session = ChargeSession(chargehistory_json[DATA_KEY][-1])

            if charge_session.start_date_time < usage_interval.end_date_time:
                fetch_interval.end_date_time = max(fetch_interval.end_date_time, charge_session.end_date_time)

    return fetch_interval


def fetch_usage(
        username: str,
        password: str,
        installation_id: str,
        usage_interval: UsageInterval,
        output_chargehistory_file_name: str) -> None:
    access_token = fetch_access_token(
        username=username,
        password=password)

    fetch_interval = determine_fetch_interval(
        access_token=access_token,
        installation_id=installation_id,
        usage_interval=usage_interval)
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
            exit(1)

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
        'output_chargehistory_file_name',
        help='the path to the output Zaptec chargehistory API response, in JSON format')

    args = parser.parse_args()
    password = getpass()

    fetch_usage(
        username=args.username,
        password=password,
        installation_id=args.installation_id,
        usage_interval=UsageInterval(args.usage_interval_start, args.usage_interval_end),
        output_chargehistory_file_name=args.output_chargehistory_file_name)


if __name__ == '__main__':
    main()
