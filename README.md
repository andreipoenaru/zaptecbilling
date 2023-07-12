# zaptecbilling


## Fetching the data

`fetcher.py` is very much WIP, but you can download the raw data at [https://api.zaptec.com/help/index.html#/ChargeHistory/get_api_chargehistory](https://api.zaptec.com/help/index.html#/ChargeHistory/get_api_chargehistory).


## Processing the data

Invoke `usage_processor.py`, e.g.:
```
$ python3 usage_processor.py data.json 2022-01-01 2023-01-01 'output.xlsx' --weekday_high_rate_interval 07:00 20:00 --saturday_high_rate_interval 07:00 13:00
```

## License

[GNU GPLv3](https://choosealicense.com/licenses/gpl-3.0/)
