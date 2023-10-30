install:
	pip install --upgrade pip
	pip install -r requirements_dev.txt

test:
	pytest --capture=tee-sys

coverage:
	pytest --cov-report term-missing --cov=config_stash tests/

lint:
	flake8 --count --verbose tests

fix:
	autopep8 --in-place --recursive tests

run-pre-commit:
	pre-commit run --all-files

update-pre-commit:
	pre-commit autoupdate