from __future__ import annotations

from swagger_codegen_fork.api.base import BaseApi

from . import get__api_installation
from . import get__api_installation_id
from . import get__api_installation_id_messagingconnectiondetails
from . import post__api_installation_id_update
from . import get__api_installation_id_hierarchy
class InstallationApi(BaseApi):
    get__api_installation = get__api_installation.make_request
    get__api_installation_id = get__api_installation_id.make_request
    get__api_installation_id_messagingconnectiondetails = get__api_installation_id_messagingconnectiondetails.make_request
    post__api_installation_id_update = post__api_installation_id_update.make_request
    get__api_installation_id_hierarchy = get__api_installation_id_hierarchy.make_request