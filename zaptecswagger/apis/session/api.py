from __future__ import annotations

from swagger_codegen_fork.api.base import BaseApi

from . import get__api_session_id
from . import post__api_session_id_priority
class SessionApi(BaseApi):
    get__api_session_id = get__api_session_id.make_request
    post__api_session_id_priority = post__api_session_id_priority.make_request