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

    commandid: int,

) -> None:
    """Send a command to the charger (require owner or service permissions)."""

    
    body = None
    

    m = ApiRequest(
        method="POST",
        path="/api/chargers/{id}/sendCommand/{commandId}".format(
            
                id=id,
            
                commandId=commandid,
            
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
            
                "default": None,
            
        },
    
        "401": {
            
                "default": None,
            
        },
    
        "403": {
            
                "default": None,
            
        },
    
    }, m)