# Following: https://docs.microsoft.com/en-us/azure/machine-learning/how-to-deploy-and-where?tabs=python
# Connect to your workspace
from azureml.core import Workspace

ws = Workspace(subscription_id="",
               resource_group="",
               workspace_name="")

# Register a model from a local file
import urllib.request
from azureml.core.model import Model

model = Model.register(ws, model_name="knn_ensemble_2", model_path="./model.joblib")
# model = Model(ws, 'knn_ensemble_2', version=1)

from azureml.core import Environment
from azureml.core.model import InferenceConfig

# Define an inference configuration
myenv = Environment.get(workspace=ws, name="AzureML-sklearn-1.0-ubuntu20.04-py38-cpu")
myenv = myenv.clone("customize_curated")

# Specify docker steps as a string. 
dockerfile = r"""
FROM mcr.microsoft.com/azureml/openmpi4.1.0-ubuntu20.04:20220516.v1

ENV AZUREML_CONDA_ENVIRONMENT_PATH /azureml-envs/sklearn-1.0
# Create conda environment
RUN conda create -p $AZUREML_CONDA_ENVIRONMENT_PATH \
    python=3.8 pip=21.3.1 -c anaconda -c conda-forge

# Prepend path to AzureML conda environment
ENV PATH $AZUREML_CONDA_ENVIRONMENT_PATH/bin:$PATH

# Install pip dependencies
RUN pip install 'matplotlib~=3.5.0' \
                'psutil~=5.8.0' \
                'tqdm~=4.62.0' \
                'pandas~=1.3.0' \
                'scipy~=1.7.0' \
                'numpy~=1.21.0' \
                'ipykernel~=6.0' \
                'azureml-core==1.41.0.post3' \
                'azureml-defaults==1.41.0' \
                'azureml-mlflow==1.41.0' \
                'azureml-telemetry==1.41.0' \
                'scikit-learn~=1.0.0' \
                'sktime'

# This is needed for mpi to locate libpython
ENV LD_LIBRARY_PATH $AZUREML_CONDA_ENVIRONMENT_PATH/lib:$LD_LIBRARY_PATH
"""

# Set base image to None, because the image is defined by dockerfile.
myenv.docker.base_image = None
myenv.docker.base_dockerfile = dockerfile

inference_config = InferenceConfig(environment=myenv, source_directory='./source_dir', entry_script='./entry_script.py')

# Define a deployment configuration
# from azureml.core.webservice import LocalWebservice

# # Local
# deployment_config = LocalWebservice.deploy_configuration(port=6789)

# Cloud
from azureml.core.webservice import AciWebservice

deployment_config = AciWebservice.deploy_configuration(
    cpu_cores=1, memory_gb=1, auth_enabled=False
)

# Deploy your machine learning model
service = Model.deploy(
    ws,
    "myservice",
    [model],
    inference_config,
    deployment_config,
    overwrite=True,
)

service.wait_for_deployment(show_output=True)
print(service.scoring_uri)