import os

from uuid import uuid4

from fabric import api
from fabric.api import env

REMOTE_ROOT = '/usr/local/demotime'
BUILD_DIR = '{}/builds'.format(REMOTE_ROOT)

env.roledefs = {
    'local': ['localhost'],
    'prod': ['demotime@45.33.113.50'],
}

# TODO: set STATIC_ROOT for collectstatic
# Setup nginx
# Solidify gunicorn


@api.roles('prod')
def deploy(branch=None):
    uuid = str(uuid4())
    with api.settings(warn_only=True):
        api.run('rm -f {}/demotime-previous')
        api.run('mv {}/demotime-current {}/demotime-previous'.format(
            REMOTE_ROOT, REMOTE_ROOT)
        )

    dir_name = ''
    # Place our code and install reqs
    with api.cd(BUILD_DIR):
        dir_name = 'demotime-{}'.format(uuid)
        api.run(
            'git clone git@github.com:f4nt/demotime.git {}'.format(
                dir_name
            )
        )
        if branch:
            api.run('cd {} && git checkout {} && cd -'.format(dir_name, branch))
        api.run('{}/bin/pip install -r {}/requirements.txt'.format(REMOTE_ROOT, dir_name))
        api.run('{}/bin/pip install -r {}/prod_requirements.txt'.format(REMOTE_ROOT, dir_name))

    # Create our symlinks
    with api.cd(REMOTE_ROOT):
        api.run('ln -s {} builds/demotime-current'.format(dir_name))
        api.run('ln -s prod_settings.py demotime-current/dt/dt/prod_settings.py')

    # Install demotime
    with api.cd(os.path.join(REMOTE_ROOT, 'demotime-current', 'demotime')):
        api.run('{}/bin/python setup.py develop'.format(REMOTE_ROOT))
