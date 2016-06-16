#! /bin/bash
../wait_for_it.sh db:5432
python3 manage.py migrate --noinput
python3 manage.py collectstatic --noinput
uwsgi --ini /home/docker/demotime/configs/uwsgi/dt_uwsgi.ini --daemonize /var/log/uwsgi/dt.log 
sed -i "s@STATIC_PATH@$STATIC_PATH@g" /etc/nginx/sites-enabled/demotime.conf
# Symlink in Django admin path
if [ "$STATIC_PATH" == "/home/docker/demotime/demotime/demotime/static" ]; then
    ln -s /usr/local/lib/python3.5/dist-packages/django/contrib/admin/static/admin /home/docker/demotime/demotime/demotime/static/admin;
fi
nginx -g "daemon off;"
