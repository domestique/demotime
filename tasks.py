import os
from invoke import run, task

LOCAL_ROOT = os.path.dirname(os.path.realpath(__file__))
DOCKER_DEV_COMMAND_ROOT = 'docker-compose -f docker-compose.yml -f docker-compose.override.yml'
DOCKER_PROD_COMMAND_ROOT = 'docker-compose -f docker-compose.yml -f docker-compose.prod.yml'


@task
def run_tests(context, test_module='demotime'):
    print("Cleaning out pycs")
    run('find . -type f -name \*.pyc -delete')
    run('cd {} && python3 manage.py test {}'.format(
        os.path.join(LOCAL_ROOT, 'dt'),
        test_module
    ))


@task
def control_docker_dev(context, cmd='up -d'):
    run('cd {} && {} {}'.format(
        LOCAL_ROOT,
        DOCKER_DEV_COMMAND_ROOT,
        cmd
    ))


@task
def load_test_data(context, filename='demotime_data.sql.gz'):
    print("This will delete all of the data in the database, and recreate it from a backup. Are you sure?")
    print("Press ctrl-c to exit, enter to continue")
    input()
    run('docker exec -i src_db_1 su - postgres -c "dropdb postgres && createdb -EUNICODE -Opostgres postgres && zcat /backups/{} | psql postgres"'.format(
        filename
    ))
    run('docker exec -i src_demotime_1 python3 manage.py migrate')
    run('docker exec -i src_demotime_1 ./reset_all_user_passwords.sh')
