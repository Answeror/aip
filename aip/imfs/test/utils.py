import os
from .const import NERV, CURRENT_PATH


def load_nerv():
    with open(os.path.join(CURRENT_PATH, NERV), 'rb') as f:
        return NERV, f.read()
