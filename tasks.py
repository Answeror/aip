import os
from aip import make


ROOT = os.path.abspath(os.path.dirname(__file__))


app = make(
    __name__,
    instance_path=os.path.join(ROOT, 'data'),
    instance_relative_config=True
)
celery = app.celery
