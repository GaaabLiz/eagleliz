import base64

from pylizlib.media.api.data.eagleapi import EAGLE_LOCALHOST_URL, EagleApi
from pylizlib.media.api.dto.eagle_dto import EagleDto
from old_code.liz_image import LizImage
from pylizlib.model.operation import Operation


class Eagleliz:
    def __init__(self, url: str = EAGLE_LOCALHOST_URL):
        self.obj = EagleApi(url)

    def get_app_info(self) -> Operation[EagleDto]:
        response = self.obj.get_app_info()
        if response.is_successful():
            resp_json: str = response.json
            eagle_obj = EagleDto.from_dict(resp_json)
            return Operation(status=True, payload=eagle_obj)
        else:
            error = response.get_error()
            return Operation(status=False, error=error)

    def add_image_from_path(self, image: LizImage) -> Operation[None]:
        # Converting image to base64
        with open(image.payload_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
        # calling api
        resp_obj = self.obj.add_image_from_path(
            path=image.payload_path,
            name=image.ai_file_name,
            tags=image.ai_tags,
            annotation=image.get_desc_plus_text(),
            modification_time=image.creation_time_timestamp,
        )
        # checking response
        if resp_obj.is_successful():
            resp_json: str = resp_obj.json
            eagle_obj = EagleDto.from_dict2(resp_json)
            if eagle_obj.status == "success":
                return Operation(status=True)
            else:
                return Operation(status=False, error="Error while adding image to eagle.")
        else:
            error = resp_obj.get_error()
            return Operation(status=False, error=error)