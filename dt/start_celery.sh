#! /bin/bash
../wait_for_it.sh rmq:5672
C_FORCE_ROOT=1 celery -A dt worker --loglevel=info
