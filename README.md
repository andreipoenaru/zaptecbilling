# zaptecbilling


## Using `run.sh`
Create an `args.sh` file and set the value of the arguments:
```
$ cp args.sh.tmpl args.sh
```

Afterwards simply run the script and you will be prompted for the Zaptec owner account password:
```
$ ./run.sh
```

## Fetching the data

Invoke `usage_fetcher.py`, e.g.:
```
$ python3 usage_fetcher.py owner@email.com installation-id 2024-01-01 2024-07-01 3 zaptec-2024H1-response.json
```


## Processing the data

Invoke `usage_processor.py`, e.g.:
```
$ python3 usage_processor.py data.json 2022-01-01 2023-01-01 'output.xlsx' --weekday_high_rate_interval 07:00 20:00 --saturday_high_rate_interval 07:00 13:00
```

## License

[GNU GPLv3](https://choosealicense.com/licenses/gpl-3.0/)
