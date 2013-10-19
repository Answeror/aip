from ..baidupcs import BaiduPCS
from ..fs import FS
from ..cascade import Cascade
from .const import ACCESS_TOKEN
from .base import Base


class TestCascade(Base):

    def __init__(self):
        Base.__init__(self, lambda: Cascade(FS(), BaiduPCS(ACCESS_TOKEN)))
