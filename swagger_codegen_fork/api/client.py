from typing import Coroutine, Union

from swagger_codegen_fork.api.adapter.base import HttpClientAdapter
from swagger_codegen_fork.api.configuration import Configuration
from swagger_codegen_fork.api.request import ApiRequest
from swagger_codegen_fork.api.response import ApiResponse


class ApiClient:
    def __init__(self, configuration: Configuration, adapter: HttpClientAdapter):
        self._configuration = configuration
        self._adapter = adapter

    def call_api(
        self, api_request: ApiRequest
    ) -> Union[ApiResponse, Coroutine[None, None, ApiResponse]]:
        method = api_request.clone(
            path=self._configuration.host + api_request.path,
        )
        return self._adapter.call(method)
