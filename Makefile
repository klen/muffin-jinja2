VIRTUAL_ENV ?= .venv

all: $(VIRTUAL_ENV)

.PHONY: help
# target: help - Display callable targets
help:
	@egrep "^# target:" [Mm]akefile

.PHONY: clean
# target: clean - Display callable targets
clean:
	rm -rf build/ dist/ docs/_build *.egg-info
	find $(CURDIR) -name "*.py[co]" -delete
	find $(CURDIR) -name "*.orig" -delete
	find $(CURDIR)/$(MODULE) -name "__pycache__" | xargs rm -rf

# ==============
#  Bump version
# ==============

.PHONY: release
VERSION?=minor
# target: release - Bump version
release: $(VIRTUAL_ENV)
	@$(VIRTUAL_ENV)/bin/bump2version $(VERSION)
	@git checkout master
	@git merge develop
	@git checkout develop
	@git push origin develop master
	@git push --tags

.PHONY: minor
minor: release

.PHONY: patch
patch:
	make release VERSION=patch

.PHONY: major
major:
	make release VERSION=major

# =============
#  Development
# =============

$(VIRTUAL_ENV): requirements/requirements.txt requirements/requirements-tests.txt
	@[ -d $(VIRTUAL_ENV) ] || python -m venv $(VIRTUAL_ENV)
	@$(VIRTUAL_ENV)/bin/pip install -e .[tests,build]
	@touch $(VIRTUAL_ENV)

.PHONY: t test
# target: test - Runs tests
t test: $(VIRTUAL_ENV)
	@$(VIRTUAL_ENV)/bin/py.test tests

.PHONY: mypy
# target: mypy - Check types
mypy: $(VIRTUAL_ENV)
	@$(VIRTUAL_ENV)/bin/mypy muffin_jinja2
