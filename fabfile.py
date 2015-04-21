import os

from uuid import uuid4

from fabric import api
from fabric.api import env

REMOTE_ROOT = '/usr/local/demotime'
REMOTE_BUILD_DIR = '{}/builds'.format(REMOTE_ROOT)

LOCAL_ROOT = os.path.dirname(os.path.realpath(__file__))

env.roledefs = {
    'local': ['localhost'],
    'prod': ['demotime@45.33.113.50'],
}


@api.roles('local')
def run_tests(test_module='demotime'):
    api.local('echo "Cleaning out pycs"')
    api.local('find . -type f -name \*.pycs -delete')
    with api.lcd(os.path.join(LOCAL_ROOT, 'dt')):
        api.local('echo "Running DemoTime tests"')
        return api.local('python manage.py test {}'.format(test_module))


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
    with api.cd(REMOTE_BUILD_DIR):
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
        api.run('ln -s {}/{} demotime-current'.format(REMOTE_BUILD_DIR, dir_name))

    # App setup stuff
    with api.cd(os.path.join(REMOTE_BUILD_DIR, dir_name, 'dt')):
        api.run('cd dt && ln -s {}/prod_settings.py .'.format(REMOTE_ROOT))
        api.run('{}/bin/python manage.py collectstatic --noinput'.format(REMOTE_ROOT))
        api.run('{}/bin/python manage.py migrate'.format(REMOTE_ROOT))
        # Restart seems finicky
        api.run('sudo stop demotime')
        api.run('sudo start demotime')
