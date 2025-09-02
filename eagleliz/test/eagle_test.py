


import unittest

import os

from dotenv import load_dotenv
from eagleliz.api.eagleliz import Eagleliz
from eagleliz.api.types import PathItem


class TestVideo(unittest.TestCase):

    def test_get_app_info(self):
        eagleliz = Eagleliz()
        op = eagleliz.get_app_info()
        assert op.status
        print(op.payload)

    def test_add_from_paths(self):
        load_dotenv()
        eagleliz = Eagleliz()
        item_1 = PathItem(
            path=os.getenv("LOCAL_IMAGE_FOR_TEST"),
            name="gatto",
            annotation="descrizoine",
            tags=["gatto", "animale"],
        )
        resp = eagleliz.add_from_paths([item_1])
        print(resp.json)




