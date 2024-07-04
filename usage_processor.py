import argparse
import json

import pandas as pd

from datetime import datetime, time, timezone
from decimal import Decimal
from enum import Enum
from functools import total_ordering
from UliPlot.XLSX import auto_adjust_xlsx_column_width

from common import ChargeSession, EnergyDetail, EnergyRate, HighRateInterval,\
    TIMESTAMP_RECORD_DELAY, UsageInterval, ZRH, is_timezone_naive


LOCALE = 'de-CH'


def process_usage(
        chargehistory_file_path: str,
        usage_interval: UsageInterval,
        output_excel_file_name: str,
        weekday_high_rate_interval: HighRateInterval = None,
        saturday_high_rate_interval: HighRateInterval = None) -> None:

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
        START_DATE_TIME = 'StartDateTime'
        COMMIT_END_DATE_TIME = 'CommitEndDateTime'
        CHARGE_SESSION_ENERGY = 'ChargeSessionEnergy'
        COMMENT = 'Comment'

        def __lt__(self, other):
            if self.__class__ is other.__class__:
                return self.value < other.value
            return NotImplemented

        def get_text(self, locale: str):
            return TABLE_COLUMNS_LOCALES[locale][self]

    TABLE_COLUMNS_LOCALES = {
        'de-CH': {
            TableColumns.DEVICE_ID: 'Ladestation Seriennummer',
            TableColumns.DEVICE_NAME: 'Ladestation Name',
            TableColumns.TIMESTAMP: 'Zeitpunkt (Europe/Zürich)',
            TableColumns.ENERGY: 'Energie (kWh)',
            TableColumns.ENERGY_RATE: 'Energietarif',
            TableColumns.START_DATE_TIME: 'Gestartet (Europe/Zürich)',
            TableColumns.COMMIT_END_DATE_TIME: 'Beendet (Europe/Zürich)',
            TableColumns.CHARGE_SESSION_ENERGY: 'Ladevorgang Energie (kWh)',
            TableColumns.COMMENT: "Hinweis",
        },
    }

    energy_details_rows = []
    for charge_session_json in chargehistory_json['Data']:
        charge_session = ChargeSession(charge_session_json)

        if charge_session.end_date_time <= usage_interval.start_date_time\
                or usage_interval.end_date_time <= charge_session.start_date_time - TIMESTAMP_RECORD_DELAY:
            # This charge session is outside the usage interval.
            continue

        charge_session.compute_energy_details_or_rate(usage_interval)

        if charge_session.optional_energy_details is None:
            assert charge_session.optional_energy_rate is not None,\
                'The charging session is missing both energy details and an explicit energy rate: %s'\
                    % charge_session_json
            energy_details_rows.append([
                charge_session.device_id,
                charge_session.device_name,
                None,
                charge_session.energy,
                charge_session.optional_energy_rate,
                charge_session.start_date_time,
                charge_session.end_date_time,
                charge_session.energy,
                charge_session.comment])
            continue

        for energy_detail in charge_session.optional_energy_details:
            if not energy_detail.is_in_usage_interval(usage_interval):
                continue
            energy_details_rows.append([
                charge_session.device_id,
                charge_session.device_name,
                energy_detail.timestamp,
                energy_detail.energy,
                energy_detail.compute_energy_rate(WEEKDAY_TO_OPTIONAL_HIGH_RATE_INTERVAL),
                charge_session.start_date_time,
                charge_session.end_date_time,
                charge_session.energy,
                charge_session.comment])

    @total_ordering
    class SummaryTableLabels(str, Enum):
        TOTAL_ENERGY = 'TotalEnergy'
        LOW_ENERGY = 'LowEnergy'
        HIGH_ENERGY = 'HighEnergy'

        def __lt__(self, other):
            if self.__class__ is other.__class__:
                return self.value < other.value
            return NotImplemented

        def get_text(self, locale: str):
            return SUMMARY_TABLE_LABELS_LOCALES[locale][self]

    SUMMARY_TABLE_LABELS_LOCALES = {
        'de-CH': {
            SummaryTableLabels.TOTAL_ENERGY: 'Gesamtenergie (kWh)',
            SummaryTableLabels.LOW_ENERGY: 'Niedertarif Energie (kWh)',
            SummaryTableLabels.HIGH_ENERGY: 'Hochtarif Energie (kWh)',
        },
    }

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
        fill_value=0,
        aggfunc='sum',
        margins=True,
        margins_name=SummaryTableLabels.TOTAL_ENERGY)
    summary_df.columns = [SummaryTableLabels.LOW_ENERGY if c == EnergyRate.LOW else c for c in summary_df.columns]
    summary_df.columns = [SummaryTableLabels.HIGH_ENERGY if c == EnergyRate.HIGH else c for c in summary_df.columns]

    print(summary_df)

    # Export the data to an .xlsx file; only formatting changes from here on.

    # Drop timezone info because Excel doesn't support datetimes w/ timezone info.
    energy_details_df[TableColumns.TIMESTAMP] = energy_details_df[TableColumns.TIMESTAMP].apply(
        lambda d: d.replace(tzinfo=None))
    energy_details_df[TableColumns.START_DATE_TIME] = energy_details_df[TableColumns.START_DATE_TIME].apply(
        lambda d: d.replace(tzinfo=None))
    energy_details_df[TableColumns.COMMIT_END_DATE_TIME] = energy_details_df[TableColumns.COMMIT_END_DATE_TIME].apply(
        lambda d: d.replace(tzinfo=None))

    with pd.ExcelWriter(output_excel_file_name) as writer:
        summary_df.columns = [c.get_text(LOCALE) for c in summary_df.columns]
        summary_df.index.names = [c.get_text(LOCALE) for c in summary_df.index.names]
        summary_df.index = summary_df.index.set_levels(
            [x.get_text(LOCALE) if isinstance(x, Enum) else x
                for x in summary_df.index.levels[0]],
                level=0,
                verify_integrity=True)
        summary_df.to_excel(writer, sheet_name='Überblick')
        auto_adjust_xlsx_column_width(summary_df, writer, sheet_name="Überblick", margin=2)

        energy_details_df[TableColumns.ENERGY_RATE] = energy_details_df[TableColumns.ENERGY_RATE].apply(
            lambda er: er.get_text(LOCALE))
        for device_id in sorted(energy_details_df[TableColumns.DEVICE_ID].unique()):
            device_energy_details_df = energy_details_df[energy_details_df[TableColumns.DEVICE_ID] == device_id]
            device_energy_details_df = device_energy_details_df.sort_values(
                by=[TableColumns.START_DATE_TIME, TableColumns.COMMIT_END_DATE_TIME, TableColumns.TIMESTAMP])
            device_energy_details_df.columns = [c.get_text(LOCALE) for c in device_energy_details_df.columns]
            device_energy_details_df.to_excel(writer, sheet_name=device_id, index=False)
            auto_adjust_xlsx_column_width(device_energy_details_df, writer, sheet_name=device_id, margin=2, index=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Process usage fetched from \'https://api.zaptec.com/api/chargehistory/\'.')

    parser.add_argument(
        'chargehistory_file_path',
        help='the path to the Zaptec chargehistory API response, in JSON format')
    parser.add_argument(
        'usage_interval_start',
        type=datetime.fromisoformat,
        help='the start of the usage reporting period, in the Europe/Zurich time zone, '
        'but without explicit time zone info; charging slots before this timestamp are ignored')
    parser.add_argument(
        'usage_interval_end',
        type=datetime.fromisoformat,
        help='the end of the usage reporting period, in the Europe/Zurich time zone, '
        'but without explicit time zone info; charging slots before this timestamp are ignored')
    parser.add_argument(
        'output_excel_file_name',
        help='the path to the output Excel file')
    parser.add_argument(
        '--weekday_high_rate_interval',
        nargs=2,
        type=time.fromisoformat,
        help='the high-rate weekdays interval, in the Europe/Zurich time zone, '
        'but without explicit time zone info; if unspecified, the whole weekday '
        'is considered low-rate',
        metavar='DATETIME')
    parser.add_argument(
        '--saturday_high_rate_interval',
        nargs=2,
        type=time.fromisoformat,
        help='the high-rate Saturday interval, in the Europe/Zurich time zone, '
        'but without explicit time zone info; if unspecified, the entire Saturday '
        'is considered low-rate',
        metavar='DATETIME')

    args = parser.parse_args()

    process_usage(
        chargehistory_file_path=args.chargehistory_file_path,
        usage_interval=UsageInterval(args.usage_interval_start, args.usage_interval_end),
        weekday_high_rate_interval=
            HighRateInterval(args.weekday_high_rate_interval[0], args.weekday_high_rate_interval[1])
            if args.weekday_high_rate_interval is not None
            else None,
        saturday_high_rate_interval=
            HighRateInterval(args.saturday_high_rate_interval[0], args.saturday_high_rate_interval[1])
            if args.saturday_high_rate_interval is not None
            else None,
        output_excel_file_name=args.output_excel_file_name)
