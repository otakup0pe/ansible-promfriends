.PHONY: lint test test-selection test-prune test-sweep test-alertmanager test-cadvisor test-delivery test-container-context test-node test-ubuntu2204 test-ubuntu2404 test-debian12 test-debian13 test-all clean distclean

VENV := .venv
BIN := $(VENV)/bin
export PATH := $(CURDIR)/$(BIN):$(PATH)

MOLECULE_SCENARIO ?= --all
CONTAINER_CONTEXT_OS ?= ubuntu
CONTAINER_CONTEXT_VERSION ?= 2404
NODE_OS ?= ubuntu
NODE_VERSION ?= 2404

$(VENV): requirements-dev.txt
	python3 -m venv $(VENV)
	$(BIN)/pip install --upgrade pip
	$(BIN)/pip install -r requirements-dev.txt
	@touch $(VENV)

lint: $(VENV)
	$(BIN)/yamllint -c .yamllint defaults tasks vars meta
	$(BIN)/ansible-lint -c .ansible-lint defaults tasks vars meta

test: lint test-selection test-prune test-sweep test-alertmanager test-cadvisor test-delivery test-all

test-selection: $(VENV)
	$(BIN)/ansible-playbook tests/image_selection.yml

test-prune: $(VENV)
	$(BIN)/ansible-playbook tests/prune_integration.yml

test-sweep: $(VENV)
	$(BIN)/ansible-playbook tests/rule_sweep.yml

test-alertmanager: $(VENV)
	$(BIN)/ansible-playbook tests/alertmanager_config.yml

test-cadvisor: $(VENV)
	$(BIN)/ansible-playbook tests/cadvisor_context.yml

test-delivery: $(VENV)
	$(BIN)/ansible-playbook tests/delivery_contract.yml

test-container-context: $(VENV)
	MOLECULE_OS=$(CONTAINER_CONTEXT_OS) MOLECULE_VERSION=$(CONTAINER_CONTEXT_VERSION) $(BIN)/molecule test -s container_context

test-node: $(VENV)
	MOLECULE_OS=$(NODE_OS) MOLECULE_VERSION=$(NODE_VERSION) $(BIN)/molecule test -s default

test-ubuntu2204: $(VENV)
	MOLECULE_OS=ubuntu MOLECULE_VERSION=2204 $(BIN)/molecule test $(MOLECULE_SCENARIO)

test-ubuntu2404: $(VENV)
	MOLECULE_OS=ubuntu MOLECULE_VERSION=2404 $(BIN)/molecule test $(MOLECULE_SCENARIO)

test-debian12: $(VENV)
	MOLECULE_OS=debian MOLECULE_VERSION=12 $(BIN)/molecule test $(MOLECULE_SCENARIO)

test-debian13: $(VENV)
	MOLECULE_OS=debian MOLECULE_VERSION=13 $(BIN)/molecule test $(MOLECULE_SCENARIO)

test-all: test-ubuntu2204 test-ubuntu2404 test-debian12 test-debian13

clean:
	$(BIN)/molecule destroy $(MOLECULE_SCENARIO) 2>/dev/null || true

distclean: clean
	rm -rf $(VENV)
