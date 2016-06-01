import os
from invoke import run, task

LOCAL_ROOT = os.path.dirname(os.path.realpath(__file__))


@task
def run_tests(test_module='demotime'):
    print("Cleaning out pycs")
    run('find . -type f -name \*.pyc -delete')
    run('cd {} && python manage.py test {}'.format(
        os.path.join(LOCAL_ROOT, 'dt'),
        test_module
    ))
