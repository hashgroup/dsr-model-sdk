test:
	python3 -m pytest
	
main-test:
	python3 tests/main.py

build:
	rm -rf dist
	python3 -m pip install --upgrade build
	python3 -m build

upload:
	python3 -m pip install --upgrade twine
	python3 -m twine check dist/*
	python3 -m twine upload dist/*