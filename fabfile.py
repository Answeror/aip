#!/usr/bin/env python
# -*- coding: utf-8 -*-


from fabric.api import run, env, cd, prefix


# the user to use for the remote commands
env.user = 'answeror'
# the servers where the commands are executed
env.hosts = ['aip.io']


def deploy():
    with cd('/www/aip/repo'):
        run('git pull')
        with prefix('pyenv virtualenvwrapper'):
            with prefix('workon aip'):
                run('python setup.py develop')
    # and finally touch the .wsgi file so that mod_wsgi triggers
    # a reload of the application
    run('touch /www/aip/repo/application.wsgi')
