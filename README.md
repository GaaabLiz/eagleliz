# EAGLELIZ
Python binding for [eagle.cool api](https://api.eagle.cool).

Currently only supports the following endpoints:
- /api/application/info
- /api/item/addFromPaths

## Installation
```bash
pip install eagleliz
```

## Async file upload helper

The package now includes `AsynchEagleApiExtended`, which extends
`AsyncEagleAPI` and adds `add_item_from_file(path, name, tags)`.

It reads a local image, converts it to a base64 data URI, and uploads it via
`POST /api/item/addFromURL`.

```python
import asyncio

from eagleliz.api import AsynchEagleApiExtended


async def main():
	client = AsynchEagleApiExtended()
	item_id = await client.add_item_from_file(
		path="/absolute/path/to/image.png",
		name="Imported from file",
		tags=["local", "upload"],
	)
	print(item_id)


asyncio.run(main())
```

