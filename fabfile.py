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
def deploy(branch='master'):
    uuid = str(uuid4())
    with api.settings(warn_only=True):
        api.run('rm -f {}/demotime-previous')
        api.run('mv {}/demotime-current {}/demotime-previous'.format(
            REMOTE_ROOT, REMOTE_ROOT)
        )

    dir_name = ''
    package_url = 'https://github.com/f4nt/demotime/archive/{}.zip'.format(branch)
    # Place our code and install reqs
    with api.cd(BUILD_DIR):
        dir_name = 'demotime-{}'.format(uuid)
        api.run('wget {}'.format(package_url))
        api.run('unzip {}.zip'.format(branch))
        api.run('mv demotime-{} {}'.format(branch, dir_name))
        api.run('{}/bin/pip install -r {}/requirements.txt'.format(REMOTE_ROOT, dir_name))
        api.run('{}/bin/pip install -r {}/prod_requirements.txt'.format(REMOTE_ROOT, dir_name))
        # Uninstall and reinstall demotime
        api.run('{}/bin/pip uninstall demotime -y'.format(REMOTE_ROOT))
        api.run('{}/bin/python {}/demotime/setup.py install'.format(REMOTE_ROOT, dir_name))
        # Cleanup
        api.run('rm -f {}.zip'.format(branch))

    # Create our symlinks
    with api.cd(REMOTE_ROOT):
        api.run('ln -s builds/{} demotime-current'.format(dir_name))
        api.run('ln -s prod_settings.py demotime-current/dt/dt/prod_settings.py')
