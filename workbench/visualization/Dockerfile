FROM docker.io/jupyter/datascience-notebook:lab-3.6.1

ENV CONDA_DIR=/opt/conda SHELL=/bin/bash NB_USER=jovyan NB_UID=1000 NB_GID=100 LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 LANGUAGE=en_US.UTF-8

RUN mamba install --quiet --yes \
    'plotly' \ 
    'boto3' \
    'sqlalchemy' \
    'psycopg2-binary' \
    'mlflow' && \
    mamba clean --all -f -y && \
    fix-permissions "${CONDA_DIR}" && \
    fix-permissions "/home/${NB_USER}"

RUN pip install --user  'jupyterlab-s3-browser' 'jupyterlab-git'

RUN jupyter serverextension enable --py jupyterlab_s3_browser