import os


CURRENT_PATH = os.path.dirname(__file__)

assert os.path.exists(os.path.join(CURRENT_PATH, 'access-token'))
with open(os.path.join(CURRENT_PATH, 'access-token'), 'rb') as f:
    ACCESS_TOKEN = f.read().decode('ascii').strip()

NERV = 'nerv_small.png'
