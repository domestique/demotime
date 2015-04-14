from uuid import uuid4

from fabric import api

REMOTE_ROOT = '/usr/local/demotime'
BUILD_DIR = '{}/builds'.format(REMOTE_ROOT)


def deploy():
    uuid = str(uuid4())
    with api.settings(warn_only=True):
        api.run('rm -f {}/demotime-previous')
        api.run('mv {}/demotime-current {}/demotime-previous'.format(
            REMOTE_ROOT, REMOTE_ROOT)
        )

    dir_name = ''
    with api.cd(BUILD_DIR):
        dir_name = 'demotime-{}'.format(uuid)
        api.run(
            'git clone git@github.com:f4nt/demotime.git {}'.format(
                dir_name
            )
        )
        api.run('{}/bin/pip install -r {}/requirements.txt'.format(REMOTE_ROOT, dir_name))
        api.run('{}/bin/pip install {}/demotime/ --upgrade'.format(REMOTE_ROOT, dir_name))

    with api.cd(REMOTE_ROOT):
        api.run('ln -s {} builds/demotime-current'.format(dir_name))
