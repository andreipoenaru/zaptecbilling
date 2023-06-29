from __future__ import annotations

from swagger_codegen_fork.api.base import BaseApi

from . import get__api_chargers
from . import get__api_chargers_id
from . import post__api_chargers_id_update
from . import get__api_chargers_id_state
from . import post__api_chargers_id_sendcommand_commandid
class ChargerApi(BaseApi):
    get__api_chargers = get__api_chargers.make_request
    get__api_chargers_id = get__api_chargers_id.make_request
    post__api_chargers_id_update = post__api_chargers_id_update.make_request
    get__api_chargers_id_state = get__api_chargers_id_state.make_request
    post__api_chargers_id_sendcommand_commandid = post__api_chargers_id_sendcommand_commandid.make_request