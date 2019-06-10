# Base Stage with installed deps
# Keep it away from environment variables. 

FROM continuumio/miniconda3 AS base

RUN apt-get update && apt-get install -y \
    wget \
    gnupg2 \
 && wget -O - https://repo.saltstack.com/apt/debian/9/amd64/latest/SALTSTACK-GPG-KEY.pub | apt-key add - \
 && echo "deb http://repo.saltstack.com/apt/debian/9/amd64/latest stretch main" > /etc/apt/sources.list.d/saltstack.list \
 && apt-get update && apt-get install -y \
    bzip2 \
    git \
    nginx \
    gcc \
    salt-minion \
    procps \
    pv \
    curl \
 && rm -rf /var/lib/apt/lists/* /etc/nginx/sites-enabled/default


# Setup Conda Environment
FROM base as conda-app
ENV TETHYS_HOME="/usr/lib/tethys" \
    CONDA_HOME="/opt/conda" \
    CONDA_ENV_NAME=tethys

ADD environment.yml ${TETHYS_HOME}/src/
WORKDIR ${TETHYS_HOME}/src
RUN ${CONDA_HOME}/bin/conda env create -n "${CONDA_ENV_NAME}" -f "environment.yml"


FROM conda-app as app

###############
# ENVIRONMENT #
###############


ARG TETHYSBUILD_DB_HOST 
ARG TETHYSBUILD_DB_PORT 
ARG TETHYSBUILD_DB_USERNAME
ARG TETHYSBUILD_DB_PASSWORD

ENV  TETHYS_PORT=80 \
     TETHYS_PUBLIC_HOST="127.0.0.1" \
     TETHYS_DB_USERNAME=$TETHYSBUILD_DB_USERNAME \
     TETHYS_DB_PASSWORD=$TETHYSBUILD_DB_PASSWORD \
     TETHYS_DB_HOST=$TETHYSBUILD_DB_HOST \
     TETHYS_DB_PORT=$TETHYSBUILD_DB_PORT \
     TETHYS_SUPER_USER="" \
     TETHYS_SUPER_USER_EMAIL="" \
     TETHYS_SUPER_USER_PASS="" \
     TETHYS_MOUNT_PATH="/"

# Misc
ENV  BASH_PROFILE=".bashrc" \
     UWSGI_PROCESSES=10 \
     CLIENT_MAX_BODY_SIZE="75M"

#########
# SETUP #
#########


###########
# INSTALL #
###########

#Setup Nginx User: 

RUN groupadd www;useradd -r -u 1011 -g www www;sed -i 's/^user.*/user www www;/' /etc/nginx/nginx.conf;

# ADD files from repo
ADD --chown=www:www resources ${TETHYS_HOME}/src/resources/
ADD --chown=www:www templates ${TETHYS_HOME}/src/templates/
ADD --chown=www:www tethys_apps ${TETHYS_HOME}/src/tethys_apps/
ADD --chown=www:www tethys_compute ${TETHYS_HOME}/src/tethys_compute/
ADD --chown=www:www tethys_config ${TETHYS_HOME}/src/tethys_config/
ADD --chown=www:www tethys_gizmos ${TETHYS_HOME}/src/tethys_gizmos/
ADD --chown=www:www tethys_portal ${TETHYS_HOME}/src/tethys_portal/
ADD --chown=www:www tethys_sdk ${TETHYS_HOME}/src/tethys_sdk/
ADD --chown=www:www tethys_services ${TETHYS_HOME}/src/tethys_services/
ADD --chown=www:www README.rst ${TETHYS_HOME}/src/
ADD --chown=www:www *.py ${TETHYS_HOME}/src/
ADD --chown=www:www production.yml ${TETHYS_HOME}/src/production.yml
# Add a .netrc file that will help retreiving GLDAS data if needed
ADD --chown=www:www docker/.netrc /root/.netrc

# Remove any apps that may have been installed in tethysapp
RUN rm -rf ${TETHYS_HOME}/src/tethys_apps/tethysapp \
  ; mkdir -p ${TETHYS_HOME}/src/tethys_apps/tethysapp
ADD --chown=www:www tethys_apps/tethysapp/__init__.py ${TETHYS_HOME}/src/tethys_apps/tethysapp/

# Run Installer
RUN /bin/bash -c '. ${CONDA_HOME}/bin/activate ${CONDA_ENV_NAME} \
  ; python setup.py develop \
  ; conda install -c conda-forge uwsgi -y'
RUN mkdir ${TETHYS_HOME}/workspaces ${TETHYS_HOME}/apps ${TETHYS_HOME}/static

# Add static files
ADD --chown=www:www static ${TETHYS_HOME}/src/static/

# Generate Inital Settings Files
RUN /bin/bash -c '. ${CONDA_HOME}/bin/activate ${CONDA_ENV_NAME} \
  ; tethys gen settings --production --allowed-host "${ALLOWED_HOST}" --db-username ${TETHYS_DB_USERNAME} --db-password ${TETHYS_DB_PASSWORD} --db-port ${TETHYS_DB_PORT} --overwrite \
  ; sed -i -e "s:#TETHYS_WORKSPACES_ROOT = .*$:TETHYS_WORKSPACES_ROOT = \"/usr/lib/tethys/workspaces\":" ${TETHYS_HOME}/src/tethys_portal/settings.py \
  ; tethys gen nginx --overwrite \
  ; tethys gen uwsgi_settings --overwrite \
  ; tethys gen uwsgi_service --overwrite \
  ; tethys manage collectstatic'


############
# CLEAN UP #
############
RUN apt-get -y remove gcc gnupg2 \
  ; apt-get -y autoremove \
  ; apt-get -y clean

#########################
# CONFIGURE  ENVIRONMENT#
#########################
ENV PATH ${CONDA_HOME}/miniconda/envs/tethys/bin:$PATH 
VOLUME ["${TETHYS_HOME}/workspaces", "${TETHYS_HOME}/keys"]
EXPOSE 80

###############*
# COPY IN SALT #
###############*
ADD docker/salt/ /srv/salt/
ADD docker/run.sh ${TETHYS_HOME}/

########
# RUN! #
########
WORKDIR ${TETHYS_HOME}
# Create Salt configuration based on ENVs
CMD bash run.sh
HEALTHCHECK --start-period=240s \
  CMD ps $(cat $(grep 'pid .*;' /etc/nginx/nginx.conf | awk '{print $2}' | awk -F';' '{print $1}')) > /dev/null && ps $(cat $(grep 'pidfile2: .*' src/tethys_portal/tethys_uwsgi.yml | awk '{print $2}')) > /dev/null;
