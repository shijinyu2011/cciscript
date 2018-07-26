Quality Center Utilities
========================

About
--------------------
This package provides CLI utilities for QC.

Installation
--------------------
The package is installed with::

  python setup.py install

Configuration
--------------------
The utilities require a configuration file under ~/.qcutilsrc. Example 
configuration is provided within the package root.

Execution
--------------------
The package installation installs the scripts under the system path. It 
is possible to execute the scripts also directly from the scripts/ 
within the source package directory.

Making modifications
--------------------
After the modifications have been made to the package:

#. Update the version::

     vim qcutils/__init__.py
     git add qcutils/__init__.py
     git ci -m 'Version update to $(python setup.py --version)'
     git push

#. Create new tag for the new version::

     git tag v$(python setup.py --version)
     git push --tags

#. Create new source distributale with::

     rm -rf qcutils.egg-info dist; python setup.py sdist --formats=gztar

#. Publish the new distributable to http://luxemburg.fp.nsn-rdnet.net/PYPI/

