test: linter

linter:
	yamllint tasks/*.yml defaults/*.yml meta/*.yml

.PHONY: test linter
