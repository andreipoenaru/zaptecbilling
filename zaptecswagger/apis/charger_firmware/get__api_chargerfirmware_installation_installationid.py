from __future__ import annotations

import datetime
import pydantic
import typing

from pydantic import BaseModel

from swagger_codegen_fork.api.base import BaseApi
from swagger_codegen_fork.api.request import ApiRequest
from swagger_codegen_fork.api import json
def make_request(self: BaseApi,


    installationid: str,

) -> typing.List[typing.Dict]:
    """Get firmware details for all chargers in the installation."""

    
    body = None
    

    m = ApiRequest(
        method="GET",
        path="/api/chargerFirmware/installation/{installationId}".format(
            
                installationId=installationid,
            
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