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

2. Modify horizon's settings file to add avidashboard. If you are in a development
   environment, then this file is horizon/openstack_dashboard/settings.py. If you
   are in a production environment, most likely it is at
   /usr/share/openstack-dashboard/openstack_dashboard/settings.py

   You have two options.

   Option I: Import enabled and update settings::

    import avidashboard.enabled    # ADD THIS LINE

    ...

    INSTALLED_APPS = list(INSTALLED_APPS)  # Make sure it's mutable
    settings.update_dashboards([
       openstack_dashboard.enabled,
       openstack_dashboard.local.enabled,
       avidashboard.enabled,      # ADD THIS LINE TOO
    ], HORIZON_CONFIG, INSTALLED_APPS)

3. Add the IP address(es) of the Avi Controller to your local_settings (typically in
   openstack_dashboard/local/local_settings.py in development environment, or at
   /etc/openstack_dashboard/local_settings.py in a production environment).
   For example::

    AVI_CONTROLLER = {"RegionA": "regiona.avi-lbaas.example.net",
                      "RegionB": "regionb.avi-lbaas.example.net", }
                  
4. Restart horizon. For example::

    $> apache2ctl restart
