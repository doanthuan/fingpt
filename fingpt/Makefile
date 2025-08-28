SHELL=/bin/bash
PYTHON=python3
TEST_DIR=./
PORT=8000
RELOAD=True
IMAGE_VERSION=latest

setup-fingpt:
	brew install poetry
	poetry install && \
	source $$(poetry env info --path)/bin/activate && \
	poetry add pre-commit

style:
	pre-commit run --all-files

test:
	$(PYTHON) -m pytest $(TEST_DIR)

run:
	echo "Running server on port $(PORT) with reload $(RELOAD)" && \
	if [ "$(RELOAD)" == "True" ]; \
	then uvicorn app.server:app --port $(PORT) --reload; \
	else uvicorn app.server:app --port $(PORT); fi

image_build:
	./cmd.sh build $(IMAGE_VERSION)

image_push:
	./cmd.sh push $(IMAGE_VERSION)

pf:
	promptfoo eval -c $(TEST_YAML)
