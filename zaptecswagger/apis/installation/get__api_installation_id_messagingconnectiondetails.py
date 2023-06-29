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

) -> typing.Dict:
    """Get connection details for connecting to the live AMQP 1.0 subscription
for charger events on an installation (requires owner or service permissions)."""

    
    body = None
    

    m = ApiRequest(
        method="GET",
        path="/api/installation/{id}/messagingConnectionDetails".format(
            
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