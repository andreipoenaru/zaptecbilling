from __future__ import annotations

import datetime
import pydantic
import typing

from pydantic import BaseModel

from swagger_codegen_fork.api.base import BaseApi
from swagger_codegen_fork.api.request import ApiRequest
from swagger_codegen_fork.api import json
def make_request(self: BaseApi,

    __request__: typing.Dict,


) -> typing.Dict:
    """Get a usage report matching the provided filter options (require installation owner permissions)."""

    
    body = __request__
    

    m = ApiRequest(
        method="POST",
        path="/api/chargehistory/installationreport".format(
            
        ),
        content_type="application/json",
        body=body,
        headers=self._only_provided({
        }),
        query_params=self._only_provided({
        }),
        cookies=self._only_provided({
        }),
    )
    return self.make_request({
    
        "200": {
            
                "application/json": typing.Dict,
            
                "text/json": typing.Dict,
            
                "text/plain": typing.Dict,
            
        },
    
        "401": {
            
                "default": None,
            
        },
    
        "403": {
            
                "default": None,
            
        },
    
    }, m)