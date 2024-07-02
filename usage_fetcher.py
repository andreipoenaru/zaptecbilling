import argparse
import requests

from datetime import datetime
from getpass import getpass
from http import HTTPStatus

from common import UsageInterval


def fetch_access_token(
        username: str,
        password: str):
    AUTH_URL = 'https://api.zaptec.com/oauth/token'
    ACCESS_TOKEN_KEY = 'access_token'

    auth_data = {
        'grant_type': 'password',
        'username': username,
        'password': password
    }

    auth_response = requests.post(AUTH_URL, data=auth_data)
    assert auth_response.status_code == HTTPStatus.OK,\
        'expected auth respose status code to be 200 (OK), but it was: %d.' % (auth_response.status_code,)

    auth_json = auth_response.json()
    assert ACCESS_TOKEN_KEY in auth_json,\
        'access token not in auth response json: %s.' % (auth_json,)

    return auth_json[ACCESS_TOKEN_KEY]


def fetch_usage(
        username: str,
        password: str,
        usage_interval: UsageInterval,
        num_charging_stations: int,
        output_chargehistory_file_name: str):
    assert num_charging_stations > 0,\
        'the number of charging stations needs to be > 0, but it was: %d.' % (num_charging_stations,)

    print(fetch_access_token(username, password)[:5])


def main():
    parser = argparse.ArgumentParser(
        description='Fetch usage data from \'https://api.zaptec.com/api/chargehistory/\'.')

    parser.add_argument(
        'username',
        help='the Zaptec account username, for calling the Zaptec API; '
        'the password will be prompted during execution')
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
        help='the number of charging stations that were active during the usage period')
    parser.add_argument(
        'output_chargehistory_file_name',
        help='the path to the output Zaptec chargehistory API response, in JSON format')

    args = parser.parse_args()
    password = getpass()

    fetch_usage(
        username=args.username,
        password=password,
        usage_interval=UsageInterval(args.usage_interval_start, args.usage_interval_end),
        num_charging_stations=args.num_charging_stations,
        output_chargehistory_file_name=args.output_chargehistory_file_name)


if __name__ == '__main__':
    main()
