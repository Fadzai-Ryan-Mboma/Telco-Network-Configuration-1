SHELL := /bin/bash

.PHONY: preflight-netgenix deploy-netgenix deploy-netgenix-dry-run

preflight-netgenix:
	$(MAKE) -C netgenix preflight

deploy-netgenix:
	$(MAKE) -C netgenix deploy-netgenix

deploy-netgenix-dry-run:
	$(MAKE) -C netgenix deploy-netgenix-dry-run
