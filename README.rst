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
   on the horizon machine or within horizon's python virtual environment. For
   example, you can install the python package created using the pip command
   as follows::

    pip install dist/avidashboard-0.2.1.dev39.tar.gz

2. Modify horizon's settings file to add avidashboard. If you are in a development
   environment, then this file is horizon/openstack_dashboard/settings.py. If you
   are in a production environment, most likely it is at
   /usr/share/openstack-dashboard/openstack_dashboard/settings.py

   Update settings with the following::

    import avidashboard.enabled    # ADD THIS LINE

    ...

    INSTALLED_APPS = [
        'avidashboard',  # ADD THIS LINE
        'openstack_dashboard',
        ...
        ...
    ]

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

4. (Optional) Enable the Avi Analytics Tab by setting the following in your
   local settings file::

    AVI_ANALYTICS_TAB_ENABLED = True
                  
5. (Optional) Enable full LBaaS panel to be the Avi UI by setting the following in your
   local settings file::

    AVI_LBAAS_FULL_UI = True

   In Juno, there was a bug in _tab_group.html template file, which causes the title
   of a tab to be shown in a tab group even when there is only tab in the tab group.
   This is fixed in later versions. To get around this issue, please update this file.
   (redhat: /usr/lib/python2.7/site-packages/horizon/templates/horizon/common/_tab_group.html,
   ubuntu: /usr/lib/python2.7/dist-packages/horizon/templates/horizon/common/_tab_group.html).
   Apply the line 5 and 13 from the Kilo version at
   https://github.com/openstack/horizon/blob/stable/kilo/horizon/templates/horizon/common/_tab_group.html

6. Restart horizon. For example::

    $> apache2ctl restart
