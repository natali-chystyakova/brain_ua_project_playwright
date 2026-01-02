.PHONY: d-project-i-run
# Make all actions needed for run project from zero.
d-project-i-run:
	@make init-config-i-project && \
	make d-run

.PHONY: d-project-i-purge
# Make all actions needed for purge project related data.
d-project-i-purge:
	@make d-purge


.PHONY: d-run
# Just run
d-run:
	@COMPOSE_DOCKER_CLI_BUILD=1 DOCKER_BUILDKIT=1 \
		COMPOSE_PROFILES=full_dev \
		docker-compose up \
			--build

.PHONY: d-run-i-local-dev
# Just run
d-run-i-local-dev:
	@COMPOSE_DOCKER_CLI_BUILD=1 DOCKER_BUILDKIT=1 \
		COMPOSE_PROFILES=local_dev \
		docker-compose \
			up --build


.PHONY: d-stop
# Stop services
d-stop:
	@COMPOSE_DOCKER_CLI_BUILD=1 DOCKER_BUILDKIT=1 \
		docker-compose down

.PHONY: d-purge
# Purge all data related with services
d-purge:
	@COMPOSE_DOCKER_CLI_BUILD=1 DOCKER_BUILDKIT=1 \
		docker-compose down --volumes --remove-orphans --rmi local --timeout 0


.PHONY: init-dev
# Init environment for development
init-dev:
	@pip install --upgrade pip && \
	pip install --requirement requirements.txt && \
	pre-commit install

.PHONY: init-config-i-project
# Init configs for project
init-config-i-project:
	@cp .env.project .env &&\
		cp docker-compose.override.project.yml docker-compose.override.yml

.PHONY: project-i-run
# Run project.
project-i-run:
	@python manage.py runserver


.PHONY: project-i-purge
project-i-purge:
	@echo Goodbye


.PHONY: pre-commit-run
# Run tools for files from commit.
pre-commit-run:
	@pre-commit run

.PHONY: pre-commit-run-all
# Run tools for all files.
pre-commit-run-all:
	@pre-commit run --all-files


.PHONY: migrations
# Make migrations
migrations:
	@python manage.py makemigrations

.PHONY: migrate
# Migrate
migrate:
	@python manage.py migrate



.PHONY: init-dev-i-create-superuser
# create superuser.
init-dev-i-create-superuser:
	@DJANGO_SUPERUSER_PASSWORD=admin123 python manage.py createsuperuser --user admin --email natali@gmail.com --no-input



.PHONY: util-i-kill-by-port
util-i-kill-by-port:
	@sudo lsof -i:8000 -Fp | head -n 1 | sed 's/^p//' | xargs sudo kill


.PHONY: parse
parse:
	@python3 modules/1_playwright_parser.py