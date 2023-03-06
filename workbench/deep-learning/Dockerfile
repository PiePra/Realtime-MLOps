FROM docker.io/jupyter/tensorflow-notebook:lab-3.6.1

RUN mamba install --quiet --yes \
    'mlflow' \ 
    'boto3' \
    'sqlalchemy' \
    'psycopg2-binary' \
    'plotly' \ 
    'jupyterlab-git' && \
    mamba clean --all -f -y && \
    fix-permissions "${CONDA_DIR}" && \
    fix-permissions "/home/${NB_USER}"
USER jovyan
RUN pip install 'jupyterlab-s3-browser' 
# 'elyra[all]'
RUN jupyter serverextension enable --py jupyterlab_s3_browser --sys-prefix
