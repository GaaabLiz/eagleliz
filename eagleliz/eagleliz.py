from dataclasses import asdict
from typing import Optional

from pylizlib.model.operation import Operation
from pylizlib.network.netres import NetResponse
from pylizlib.network.netutils import exec_get, exec_post

from eagleliz.types import EagleDto, PathItem

EAGLE_PORT = "41595"
EAGLE_LOCALHOST_URL = "http://localhost:" + EAGLE_PORT


class Eagleliz:

    def __init__(self, url: str = EAGLE_LOCALHOST_URL):
        self.url = url

    # Utils ------------------------------------------------

    def reject_none(self, d: dict):
        return {k:v for k, v in d.items() if not v is None}

    # Application -------------------------------------------

    def get_app_info_api(self) -> NetResponse:
        api_url = self.url + "/api/application/info"
        return exec_get(api_url)

    def get_app_info(self) -> Operation[EagleDto]:
        response = self.get_app_info_api()
        if response.is_successful():
            resp_json: str = response.json
            eagle_obj = EagleDto.from_dict(resp_json)
            return Operation(status=True, payload=eagle_obj)
        else:
            error = response.get_error()
            return Operation(status=False, error=error)


    # Items --------------------------------------------------

    def add_from_paths(
            self,
            items: list[PathItem],
            folder_id: Optional[str] = None,
    ):
        json = self.reject_none({
            "items": [asdict(item) for item in items],
            "folderId": folder_id,
        })
        api_url = self.url + "/api/item/addFromPaths"
        return exec_post(api_url, json)