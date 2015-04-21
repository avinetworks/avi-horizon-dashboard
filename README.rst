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

2. Modify horizon's settings file to add avidashboard. You have two options.

   Option I: Import enabled and update settings::

    import avidashboard.enabled    # ADD THIS LINE

    ...

    INSTALLED_APPS = list(INSTALLED_APPS)  # Make sure it's mutable
    settings.update_dashboards([
       openstack_dashboard.enabled,
       openstack_dashboard.local.enabled,
       avidashboard.enabled,      # ADD THIS LINE TOO
    ], HORIZON_CONFIG, INSTALLED_APPS)


   Option II: Just add to INSTALLED_APPS::

    INSTALLED_APPS = [
        'avidashboard.dashboards.project',  # Add this line
        'openstack_dashboard',
        ...
        ...
    ]
