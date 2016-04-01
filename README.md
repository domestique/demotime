[![Build Status](https://travis-ci.org/f4nt/demotime.svg?branch=master)](https://travis-ci.org/f4nt/demotime)

Demotime application idea we're fleshing out

Getting Started
=====================================

Steps to get the project running

* Setup a new virtualenv `virtualenv demotime`
* Clone this repo `git clone <url> demotime/src`
* Activate the new virtualenv `cd demotime && . bin/activate`
* Install the requirements `cd src && pip install -r requirements.txt`
* Set up testing requirements `pip install -r testing_requirements.txt`
* Set up for development `python demotime/setup.py develop`
* Create the db `python dt/manage.py migrate`
* Set up an administrator `python dt/manage.py createsuperuser`
* Startup the server `python dt/manage.py runserver`
* Optionally: `DT_URL=localhost:8008 python manage.py runserver 8008` to run on a different port and have emails still work fine
* Login via the admin at http://localhost:8000/admin/ (Proper logins coming later)
* Create a review via http://localhost:8000/create/
* Wait for cooler features.
