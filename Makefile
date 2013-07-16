PACKAGE=doorstop

develop: depends
	python setup.py develop

install: depends
	python setup.py install

depends: coverage
	pip install  --download-cache=/tmp/pip virtualenv epydoc nose pep8 pylint python-veracity
	

##############################################################################
# issue: coverage results are incorrect in Linux
# tracker: https://bitbucket.org/ned/coveragepy/issue/164
# workaround: install the latest code from bitbucket.org until "coverage>3.6"
ifeq ($(shell uname),Linux)

coverage: /tmp/coveragepy
	cd /tmp/coveragepy; pip install --download-cache=/tmp/pip --requirement requirements.txt; python setup.py install
	
/tmp/coveragepy:
	cd /tmp; hg clone https://bitbucket.org/ned/coveragepy

else

coverage:
	pip install --download-cache=/tmp/pip coverage

endif
##############################################################################
	
publish: clean
	python setup.py register sdist upload

##############################################################################
# issue: epydoc does not install a working CLI on Windows
# tracker: http://sourceforge.net/p/epydoc/bugs/345
# workaround: call the globally installed epydoc.py file directly
ifeq ($(OS),Windows_NT)

doc: depends
	export python C:\\Python27\\Scripts\\epydoc.py --config setup.cfg

else

doc: depends
	export epydoc --config setup.cfg

endif
##############################################################################

test: develop
	nosetests
	
check: doc
	pep8 --ignore=E501 $(PACKAGE)
	pylint $(PACKAGE) --include-ids yes --reports no --disable W0142,W0511,I0011,R,C

poller: depends
	vv-poller --daemon

builder: depends
	vv-builder --daemon --env $(VV_ENV)

clean:
	rm -rf *.egg-info dist build .coverage */*.pyc */*/*.pyc apidocs env coveragepy
