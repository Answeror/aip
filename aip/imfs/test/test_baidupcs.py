from ..baidupcs import BaiduPCS
from .const import ACCESS_TOKEN
from .base import Base


class TestPCS(Base):

    def __init__(self):
        Base.__init__(self, lambda: BaiduPCS(ACCESS_TOKEN))
