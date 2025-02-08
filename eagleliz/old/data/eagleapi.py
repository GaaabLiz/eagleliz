from pylizlib.network.netutils import exec_get, exec_post




class EagleApi:

    def __init__(self, url: str = EAGLE_LOCALHOST_URL):
        self.url = url
        pass

    def get_app_info(self):
        api_url = self.url + "/api/application/info"
        return exec_get(api_url)

    def add_image_from_path(
            self,
            path: str,
            name: str,
            tags: list[str],
            annotation: str,
            modification_time: float,
    ):
        api_url = self.url + "/api/item/addFromPath"
        payload = {
            "path": path,
            "name": name,
            "tags": tags,
            "annotation": annotation,
            "modification_time": modification_time
        }
        return exec_post(api_url, payload, False)
