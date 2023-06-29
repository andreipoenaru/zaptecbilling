from __future__ import annotations

import datetime
import pydantic
import typing

from pydantic import BaseModel

from swagger_codegen_fork.api.base import BaseApi
from swagger_codegen_fork.api.request import ApiRequest
from swagger_codegen_fork.api import json
def make_request(self: BaseApi,


    installationid: str = ...,

    userid: str = ...,

    chargerid: str = ...,

    from1: datetime.datetime = ...,

    to: datetime.datetime = ...,

    groupby: int = ...,

    detaillevel: int = ...,

    sortproperty: str = ...,

    sortdescending: bool = ...,

    pagesize: int = ...,

    pageindex: int = ...,

    includedisabled: bool = ...,

    exclude: typing.List[str] = ...,

) -> typing.Dict:
    """Get a list of all completed charge sessions accessible by the current user matching 
the filter options."""

    
    body = None
    

    m = ApiRequest(
        method="GET",
        path="/api/chargehistory".format(
            
        ),
        content_type=None,
        body=body,
        headers=self._only_provided({
        }),
        query_params=self._only_provided({
                "InstallationId": installationid,
            
                "UserId": userid,
            
                "ChargerId": chargerid,
            
                "From": from1,
            
                "To": to,
            
                "GroupBy": groupby,
            
                "DetailLevel": detaillevel,
            
                "SortProperty": sortproperty,
            
                "SortDescending": sortdescending,
            
                "PageSize": pagesize,
            
                "PageIndex": pageindex,
            
                "IncludeDisabled": includedisabled,
            
                "Exclude": exclude,
            
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