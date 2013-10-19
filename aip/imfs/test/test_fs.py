from ..fs import FS
from .base import Base


class TestFS(Base):

    def __init__(self):
        Base.__init__(self, FS)
