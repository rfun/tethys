{% set CONDA_ENV_NAME = salt['environ.get']('CONDA_ENV_NAME') %}
{% set CONDA_HOME = salt['environ.get']('CONDA_HOME') %}
{% set TETHYS_HOME = salt['environ.get']('TETHYS_HOME') %}



salt://scripts/run_install.sh:
  cmd.script:
    - env:
      - CONDA_HOME: {{ CONDA_HOME }}
      - CONDA_ENV_NAME: {{ CONDA_ENV_NAME }}
      - TETHYS_HOME: {{ TETHYS_HOME }}
    - unless: /bin/bash -c "[ -f "/usr/lib/tethys/app_setup_complete" ];"


Flag_Complete_Setup_Apps:
  cmd.run:
    - name: touch /usr/lib/tethys/app_setup_complete
    - shell: /bin/bash