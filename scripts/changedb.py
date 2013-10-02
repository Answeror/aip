import os
import sys
import changedb_conf as conf

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
data_path = os.path.join(project_root, 'data')

sys.path.insert(0, project_root)
from aip import make

sapp = make(
    config={'SQLALCHEMY_DATABASE_URI': conf.src_uri},
    dbmode=True,
    instance_path=data_path,
    instance_relative_config=True
)
dapp = make(
    config={'SQLALCHEMY_DATABASE_URI': conf.dst_uri},
    dbmode=True,
    instance_path=data_path,
    instance_relative_config=True
)
src = sapp.store.db
dst = dapp.store.db

for name in (
    'tagged',
    'user',
    'openid',
    'plus'
):
    print('deal %s' % name)
    data = src.engine.execute(src.metadata.tables[name].select()).fetchall()
    data = list(data)
    print('fetched')
    if data:
        step = 10000
        for begin in range(0, len(data), step):
            rows = data[begin:begin + step]
            dst.engine.execute(dst.metadata.tables[name].insert(), rows)


for name in (
    'user',
    'entry',
    'post',
    'tag'
):
    print('update %s sequence' % name)
    dst.engine.execute('select setval(\'{0}_id_seq\', max(id)+1) from "{0}";'.format(name))
