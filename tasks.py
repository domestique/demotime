import os
from invoke import task, util

LOCAL_ROOT = os.path.dirname(os.path.realpath(__file__))
DOCKER_DEV_COMMAND_ROOT = 'docker-compose -f docker-compose.yml -f docker-compose.override.yml'
DOCKER_PROD_COMMAND_ROOT = 'docker-compose -f docker-compose.yml -f docker-compose.prod.yml'


@task
def control_docker_dev(ctx, cmd='up -d'):
    ctx.run('cd {} && {} {}'.format(
        LOCAL_ROOT,
        DOCKER_DEV_COMMAND_ROOT,
        cmd
    ))


@task
def run_tests(ctx, test_module='demotime', opts='', pty=True):
    print("Cleaning out pycs")
    ctx.run('find . -type f -name \*.pyc -delete')
    with util.cd(os.path.join(LOCAL_ROOT, 'dt')):
        ctx.run(
            'TESTS=true coverage run --source=demotime manage.py test {} {}'.format(
                test_module, opts
            ),
            pty=pty
        )
        ctx.run('coverage xml')


@task
def load_test_data(ctx, filename='demotime_test_data.sql.gz'):
    print("This will delete all of the data in the database, and recreate it from a backup. Are you sure?")
    print("Press ctrl-c to exit, enter to continue")
    input()
    ctx.run('cp data/{} ~/dt_backups/'.format(filename))
    ctx.run('docker exec -i src_db_1 su - postgres -c "dropdb postgres && createdb -EUNICODE -Opostgres postgres && zcat /backups/{} | psql postgres"'.format(
        filename
    ))
    ctx.run('docker exec -i src_demotime_1 python3 manage.py migrate')
    ctx.run('docker restart src_demotime_1')
    ctx.run('docker restart src_demotime_celery_1')
    ctx.run('rm -f ~/dt_backups/{}'.format(filename))


@task
def purge_docker_emails(ctx):
    print('Deleting the following email files')
    ctx.run('docker exec src_demotime_1 ls -l /usr/local/demotime/static/emails/')
    ctx.run('docker exec src_demotime_1 /home/docker/demotime/dt/purge_emails.sh')
    print('Deletion complete')
    ctx.run('docker exec src_demotime_1 ls -l /usr/local/demotime/static/emails/')
