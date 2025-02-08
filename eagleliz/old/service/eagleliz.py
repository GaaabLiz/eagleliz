import base64

from eagleliz.old.data.eagleapi import EagleApi
from eagleliz.old.dto.eagle_dto import EagleDto


class Eagleliz:
    def __init__(self, url: str = EAGLE_LOCALHOST_URL):
        self.obj = EagleApi(url)



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




# def check_eagle() -> EagleStatus | None:
#     resp_obj = eagleapi.get_app_info()
#     if resp_obj.is_successful():
#         status = resp_obj.json.get("status")
#         if status == "success":
#             rich.print("Eagle instance is running.")
#             data_json = resp_obj.json.get("data")
#             eagle_obj = EagleStatus(
#                 version=data_json.get("version"),
#                 execPath=data_json.get("execPath", None),
#                 prereleaseVersion=data_json.get("prereleaseVersion"),
#                 buildVersion=data_json.get("buildVersion"),
#                 platform=data_json.get("platform")
#             )
#             # rich.print("Eagle running on path " + "[cyan]" + eagle_obj.execPath + "[/cyan].")
#             return eagle_obj
#         else:
#             rich.print("Eagle response status is not successful. Please check the eagle instance.")
#             return None
#     else:
#         error = resp_obj.get_error()
#         rich.print("Error while connecting to local eagle instance: " + "[red]" + error + "[/red]")
#         return None

#
# def check_eagle() -> EagleDto | None:
#     resp_obj = eagleapi.get_app_info()
#     if resp_obj.is_successful():
#         resp_json: str = resp_obj.json
#         eagle_obj = EagleDto.from_dict(resp_json)
#         if eagle_obj.status == "success":
#             rich.print("Found Eagle instance version " + "[cyan]" + eagle_obj.data.version + "[/cyan].")
#             rich.print("Eagle instance is running.")
#             return eagle_obj
#         else:
#             rich.print("Eagle response status is not successful. Please check the eagle instance.")
#             return None
#     else:
#         error = resp_obj.get_error()
#         rich.print("Error while connecting to local eagle instance: " + "[red]" + error + "[/red]")
#         return None
#
#
# def upload_image(image: AilizImage) -> EagleDto | None:
#
#     # Converting image to base64
#     with open(image.path, "rb") as image_file:
#         encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
#
#     # calling api
#     resp_obj = eagleapi.add_image_from_path(
#         path=image.path,
#         name=image.ai_file_name,
#         tags=image.ai_tags,
#         annotation=image.get_desc_plus_text(),
#         modification_time=image.creation_time_timestamp,
#     )
#     print(resp_obj.json)
#     print("code: " + str(resp_obj.code))
#     print("type: " + str(resp_obj.type))
#
#     # checking response
#     if resp_obj.is_successful():
#         resp_json: str = resp_obj.json
#         eagle_obj = EagleDto.from_dict2(resp_json)
#         if eagle_obj.status == "success":
#             rich.print("Image uploaded successfully to Eagle instance with id: " + "[cyan]" + eagle_obj.data2 + "[/cyan].")
#             return eagle_obj
#         else:
#             rich.print("Eagle response status is not successful. Please check the eagle instance.")
#             return None
#     else:
#         error = resp_obj.get_error()
#         rich.print("Error while connecting to local eagle instance: " + "[red]" + error + "[/red]")
#         return None
