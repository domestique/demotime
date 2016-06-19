FROM ubuntu:xenial
MAINTAINER Mark Rogers <f4nt@f4ntasmic.com>

ENV LANG=C.UTF-8
RUN dpkg-divert --local --rename --add /sbin/initctl && \
    apt-get update && \
    apt-get -y install build-essential python3 python3-dev python3-setuptools git \
        ca-certificates libpq-dev libjpeg62-dev libjpeg62 libfreetype6 nginx cron \
        libfreetype6-dev zlib1g zlib1g-dev libncurses5-dev libncurses5 libffi-dev vim && \
    /usr/bin/easy_install3 -UaZ pip && \
    mkdir -p /home/docker/demotime/ /var/log/uwsgi /usr/local/demotime/static /usr/local/demotime/media && \
    touch /var/log/cron.log 

ADD . /home/docker/demotime/
WORKDIR /home/docker/demotime/demotime/
RUN /usr/local/bin/pip3.5 install -r ../requirements.txt -r ../prod_requirements.txt -r ../testing_requirements.txt && \
    python3 setup.py develop
WORKDIR /home/docker/demotime/dt
RUN unlink /etc/nginx/sites-enabled/default && \
    ln -s /home/docker/demotime/configs/nginx/demotime.conf /etc/nginx/sites-enabled

cmd ["./startup.sh"]
