from __future__ import annotations

from swagger_codegen_fork.api.base import BaseApi

from . import get__api_chargehistory
from . import get__api_chargehistory_installationreport
from . import post__api_chargehistory_installationreport
class ChargeHistoryApi(BaseApi):
    get__api_chargehistory = get__api_chargehistory.make_request
    get__api_chargehistory_installationreport = get__api_chargehistory_installationreport.make_request
    post__api_chargehistory_installationreport = post__api_chargehistory_installationreport.make_request