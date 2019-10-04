{% set TETHYS_HOME = salt['environ.get']('TETHYS_HOME') %}
{% set NGINX_USER = salt['environ.get']('NGINX_USER') %}
{% set CONDA_HOME = salt['environ.get']('CONDA_HOME') %}

uwsgi:
  cmd.run:
    - name: {{ CONDA_HOME }}/envs/tethys/bin/uwsgi --yaml {{ TETHYS_HOME}}/src/tethys_portal/tethys_uwsgi.yml --uid {{ NGINX_USER }} --gid {{ NGINX_USER }} --enable-threads
    - bg: True
    - ignore_timeout: True

nginx:
  cmd.run:
    - name: nginx -g 'daemon off;'
    - bg: True
    - ignore_timeout: True