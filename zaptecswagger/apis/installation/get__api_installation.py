from __future__ import annotations

import datetime
import pydantic
import typing

from pydantic import BaseModel

from swagger_codegen_fork.api.base import BaseApi
from swagger_codegen_fork.api.request import ApiRequest
from swagger_codegen_fork.api import json
def make_request(self: BaseApi,


    roles: int = ...,

    installationtype: int = ...,

    excludeifvisibleforusergrouplookupkey: str = ...,

    namefilter: str = ...,

    returnidnameonly: bool = ...,

    sortproperty: str = ...,

    sortdescending: bool = ...,

    pagesize: int = ...,

    pageindex: int = ...,

    includedisabled: bool = ...,

    exclude: typing.List[str] = ...,

) -> typing.Dict:
    """Get all installations accessible by the current user matching the filter options."""

    
    body = None
    

    m = ApiRequest(
        method="GET",
        path="/api/installation".format(
            
        ),
        content_type=None,
        body=body,
        headers=self._only_provided({
        }),
        query_params=self._only_provided({
                "Roles": roles,
            
                "InstallationType": installationtype,
            
                "ExcludeIfVisibleForUserGroupLookupKey": excludeifvisibleforusergrouplookupkey,
            
                "NameFilter": namefilter,
            
                "ReturnIdNameOnly": returnidnameonly,
            
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