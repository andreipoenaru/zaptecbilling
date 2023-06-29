from zaptecswagger import new_client, Configuration
from swagger_codegen_fork.api.adapter.requests import RequestsAdapter
from swagger_codegen_fork.api.configuration import Hook
from swagger_codegen_fork.api.request import ApiRequest

class ApiKeyHook:
    api_key = "fake_api_key"

    def add_api_key(self, request: ApiRequest) -> ApiRequest:
        return request.clone(headers=dict(request.headers, **{'ApiKey': self.api_key}))


def main():
    client = new_client(RequestsAdapter(),
                        Configuration(
                            host="https://api.zaptec.com/",
                            hooks={Hook.request: [ApiKeyHook().add_api_key]}))
    client.charge_history.get__api_chargehistory()
    # client.charge_history.post__api_chargehistory_installationreport({})


if __name__ == '__main__':
    main()
