from eagleliz.api.eaglelizapi import EagleAPI, EagleAPIError

def test_get_application_info():
    api = EagleAPI()
    try:
        info = api.get_application_info()
        print(f"Eagle Version: {info.version}")
        print(f"Platform: {info.platform}")
        print(f"Executable Path: {info.execPath}")
    except EagleAPIError as e:
        print(f"Failed to fetch application info: {e}")

if __name__ == "__main__":
    test_get_application_info()
