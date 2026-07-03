SHELL := /bin/bash

.PHONY: preflight deploy-netgenix deploy-netgenix-dry-run

preflight:
	./scripts/deploy-netgenix.sh --preflight-only

deploy-netgenix:
	./scripts/deploy-netgenix.sh

deploy-netgenix-dry-run:
	./scripts/deploy-netgenix.sh --dry-run
