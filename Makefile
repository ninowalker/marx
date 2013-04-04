
all: test bdist_egg

test:
	python setup.py nosetests

debug_test:
	python setup.py nosetests --pdb --pdb-failures

bdist_egg:
	python setup.py bdist_egg