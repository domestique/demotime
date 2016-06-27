[![Build Status](https://travis-ci.org/domestique/demotime.svg?branch=master)](https://travis-ci.org/f4nt/demotime)
[![codecov](https://codecov.io/gh/domestique/demotime/branch/master/graph/badge.svg)](https://codecov.io/gh/f4nt/demotime)

DemoTime - built by Danny Peck and Mark Rogers of Domestique Studios

[Trello Board](https://trello.com/b/k9PNajpl) - Our Issue Tracker

Requirements
=====================================

Tools Required:

* Git (of course)
* Docker
* Python 3
* Postgres
* Virtualenv

Getting Started
=====================================

Initial Steps:

* Setup a new virtualenv `virtualenv demotime`
* Clone this repo `git clone <url> demotime/src`
* Activate the new virtualenv `cd demotime && . bin/activate`
* Install the requirements `cd src && pip install -r requirements.txt`
* Set up testing requirements `pip install -r testing_requirements.txt`
* Set up for development `python demotime/setup.py develop`

Local Python Setup - Running tests, debugging, etc:

* Create the db `python dt/manage.py migrate`
* Set up an administrator `python dt/manage.py createsuperuser`
* Startup the server `python dt/manage.py runserver`
* Optionally: `DT_URL=localhost:8008 python manage.py runserver 8008` to run on a different port and have emails still work fine
* Login via the admin at http://localhost:8033/

Docker Setup:

* If using Docker on Mac with Virtualbox, be sure to map port 8033
* `cd src`
* Create two Docker data volumes: 
    - `docker volume create --name dt_static_data`
    - `docker volume create --name dt_pg_data`
* Startup with docker-compose: `invoke control_docker_dev`
* To stop the containers: `invoke control_docker_dev --cmd=down`
* Login via http://localhost:8033/
