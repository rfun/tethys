#!/bin/bash

. ${CONDA_HOME}/bin/activate ${CONDA_ENV_NAME}

tethys install -r ${TETHYS_HOME}/src/production.yml

tethys manage collectstatic --noinput

