#!/bin/bash

# Load environment variables from .env file
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

if [ "$1" = "test" ]; then
  # Run all the tests
  python -m pytest "${@:2}"
  if [ $? -ne 0 ]; then
    echo "Tests failed"
    exit 1
  fi

elif [ "$1" = "run" ]; then
    # Run the application locally
  uvicorn app.server:app --port ${PORT:-8000} --reload "${@:2}"

elif [ "$1" = "build" ]; then
  # Run integration tests first
  echo "Running integration tests..."
  python integration_tests/runner.py 127.0.0.1 8001
  if [ $? -ne 0 ]; then
    echo "Integration tests failed"
    exit 1
  fi
  # Build the Docker image
  IMAGE_VERSION="$2"
  GIT_HASH=$(git rev-parse HEAD)
  IMAGE_TAG=${IMAGE_VERSION}.${GIT_HASH::7}
  IMAGE_NAME="crsdbxaz755.azurecr.io/fin-gpt:${IMAGE_TAG}"
  echo "Building Docker image: ${IMAGE_NAME}"
  docker build -t "${IMAGE_NAME}" --target runner .

elif [ "$1" = "push" ]; then
  # Push the Docker image to the Azure Container Registry
  az acr login --name crsdbxaz755.azurecr.io
  IMAGE_VERSION="$2"
  GIT_HASH=$(git rev-parse HEAD)
  IMAGE_TAG=${IMAGE_VERSION}.${GIT_HASH::7}
  IMAGE_NAME="crsdbxaz755.azurecr.io/fin-gpt:${IMAGE_TAG}"
  echo "Pushing Docker image: ${IMAGE_NAME}"
  docker push "${IMAGE_NAME}"

else
  # Print an error message if the argument is invalid
  echo "Invalid argument: $1"
  echo "Usage: exec.sh test"
  exit 1
fi
