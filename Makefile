set_env_vars := USER_NAME=$(shell id -un) USER_ID=$(shell id -u) GROUP_ID=$(shell id -g) GROUP_NAME=$(shell id -gn)

build:
	$(set_env_vars) docker compose build
.PHONY: build

run:
	$(set_env_vars) docker compose run --rm app bash
.PHONY: run