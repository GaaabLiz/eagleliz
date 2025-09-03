import json
import os
from datetime import datetime
from pathlib import Path

import requests
import rich


def upload_asset_to_immich(
        api_key: str,
        immich_url: str,
        media: Path,
):             # replace with a valid api key
    BASE_URL = f'{immich_url}/api'  # replace as needed

    stats = os.stat(media)

    rich.print(f"Uploading {media} to Immich...")

    headers = {
        'Accept': 'application/json',
        'x-api-key': api_key
    }

    data = {
        'deviceAssetId': f'{media}-{stats.st_mtime}',
        'deviceId': 'python',
        'fileCreatedAt': datetime.fromtimestamp(stats.st_mtime),
        'fileModifiedAt': datetime.fromtimestamp(stats.st_mtime),
        'isFavorite': 'false',
    }

    files = {
        'assetData': open(media, 'rb')
    }

    response = requests.post(
        f'{BASE_URL}/assets', headers=headers, data=data, files=files)

    status_code = response.status_code
    rich.print(f"Upload response code: {status_code}")

    return response.status_code == 200 or response.status_code == 201, response.json().get('id', None)


def update_immich_asset(
        api_key: str,
        immich_url: str,
        asset_id: str,
        description: str
):
    BASE_URL = f'{immich_url}/api/assets/{asset_id}'

    rich.print(f"Updating Immich asset {asset_id}...")

    payload = json.dumps({
        "description": description,
    })

    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'x-api-key': api_key
    }

    response = requests.request("PUT", BASE_URL, headers=headers, data=payload)

    rich.print(f"Updating asset status code: {response.status_code}")
    return response.status_code == 200 or response.status_code == 201