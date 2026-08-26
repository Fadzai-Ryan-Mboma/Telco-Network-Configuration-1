SHELL := /bin/bash
COMPOSE := docker compose
COMPOSE_BUILD := docker compose build --builder default

.PHONY: up down restart logs ps build preflight deploy-netgenix deploy-netgenix-dry-run

up:
	$(COMPOSE_BUILD)
	$(COMPOSE) up -d --no-build

down:
	$(COMPOSE) down

restart:
	$(COMPOSE) down
	$(COMPOSE_BUILD)
	$(COMPOSE) up -d --no-build

logs:
	$(COMPOSE) logs -f

ps:
	$(COMPOSE) ps

build:
	$(COMPOSE_BUILD)

preflight:
	./scripts/deploy-netgenix.sh --preflight-only

deploy-netgenix:
	./scripts/deploy-netgenix.sh

deploy-netgenix-dry-run:
	./scripts/deploy-netgenix.sh --dry-run
