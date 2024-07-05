#!/bin/sh

source args.sh

python3 usage_fetcher.py $USERNAME $INSTALLATION_ID $USAGE_INTERVAL_START \
    $USAGE_INTERVAL_END $NUM_CHARGING_STATIONS "$CHARGEHISTORY_FILE_NAME"

python3 usage_processor.py "$CHARGEHISTORY_FILE_NAME" $USAGE_INTERVAL_START \
    $USAGE_INTERVAL_END "$EXCEL_FILE_NAME" --weekday_high_rate_interval \
    $WEEKDAY_HIGH_RATE_INTERVAL