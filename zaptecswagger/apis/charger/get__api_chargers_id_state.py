from __future__ import annotations

import datetime
import pydantic
import typing

from pydantic import BaseModel

from swagger_codegen_fork.api.base import BaseApi
from swagger_codegen_fork.api.request import ApiRequest
from swagger_codegen_fork.api import json
def make_request(self: BaseApi,


    id: str,

) -> typing.List[typing.Dict]:
    """Get the current state properties (observations) for the provided charger
(requires owner or service permissions)."""

    
    body = None
    

    m = ApiRequest(
        method="GET",
        path="/api/chargers/{id}/state".format(
            
                id=id,
            
        ),
        content_type=None,
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
            
                "application/json": typing.List[typing.Dict],
            
                "text/json": typing.List[typing.Dict],
            
                "text/plain": typing.List[typing.Dict],
            
        },
    
        "401": {
            
                "default": None,
            
        },
    
        "403": {
            
                "default": None,
            
        },
    
    }, m)