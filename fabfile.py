#!/usr/bin/env python
# -*- coding: utf-8 -*-


from fabric.api import run, env, cd, prefix, settings


# the user to use for the remote commands
env.user = 'answeror'
# the servers where the commands are executed
env.hosts = ['aip.io']


def runbg(cmd, sockname="dtach"):
    return run('dtach -n `mktemp -u /tmp/%s.XXXX` %s'  % (sockname,cmd))


def kill(name):
    run("ps auxww | grep %s | grep -v \"grep\" | awk '{print $2}' | xargs kill >& /dev/null" % name)


def deploy():
    with settings(warn_only=True):
        kill('rqworker')
        kill('aiplog')
    with cd('/www/aip/repo'):
        run('git pull')
        with prefix('pyenv virtualenvwrapper'):
            with prefix('workon aip'):
                run('python setup.py develop')
                #runbg('celery -A tasks worker')
                runbg('aiplog')
                for i in range(8):
                    runbg('rqworker')
    # and finally touch the .wsgi file so that mod_wsgi triggers
    # a reload of the application
    run('touch /www/aip/repo/application.wsgi')


def gunicorn():
    with settings(warn_only=True):
        kill('rqworker')
        kill('aiplog')
        kill('gunicorn')
    with cd('/www/aip/repo'):
        run('git pull')
        with prefix('pyenv virtualenvwrapper'):
            with prefix('workon aip'):
                run('python setup.py develop')
                #runbg('celery -A tasks worker')
                runbg('aiplog')
                for i in range(8):
                    runbg('rqworker')
                runbg('gunicorn -t 600 -w 4 -k gunicorn_worker.Worker --keep-alive 5 gunicorn_app:app')
