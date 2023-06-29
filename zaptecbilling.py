from zaptecswagger import new_client, Configuration
from swagger_codegen_fork.api.adapter.requests import RequestsAdapter


def main():
    client = new_client(RequestsAdapter(), Configuration(host="https://api.zaptec.com/"))
    # client.charge_history.post__api_chargehistory_installationreport({})
    client.charge_history.get__api_chargehistory()


if __name__ == '__main__':
    main()
