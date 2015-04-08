[![Build Status](https://travis-ci.org/f4nt/demotime.svg?branch=master)](https://travis-ci.org/f4nt/demotime)

Demotime application idea we're fleshing out

Getting Started
=====================================

Steps to get the project running:

* Setup a new virtualenv
* Clone this repo
* Install the requirements: `pip install -r requirements.txt`
* Create the db: `python manage.py syncdb && python manage.py migrate`
* Startup the server: `python manage.py runserver`
* Login via the admin at http://localhost:8000/admin/ (Proper logins coming later)
* Create a review via http://localhost:8000/create/ 
* Wait for cooler features.

For running unit tests, you'll need to install the test reqs too:

* `pip install -r testing_requirements.txt`
