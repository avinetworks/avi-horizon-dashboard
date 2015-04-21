===============================
avidashboard
===============================

Avi Horizon UI bits

* Free software: Apache license

Features
--------

* TODO


Howto
-----

1. Package the avidashboard by running::

    python setup.py sdist

   This will create a python egg in the dist folder, which can be used to install
   on the horizon machine or within horizon's  python virtual environment.

2. Modify horizon's settings file to add avidashboard to INSTALLED_APPS::

    INSTALLED_APPS = [
        'avidashboard.dashboards.project',  # Add this line
        'openstack_dashboard',
        ...
        ...
    ]
