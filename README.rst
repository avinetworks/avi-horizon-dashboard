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

1. Obtain the avidashboard PIP package for your version of horizon from the
   `releases page`_
.. _releases page: https://github.com/avinetworks/avi-horizon-dashboard/releases/tag/latest

2. Install the python package using the pip command as follows::

    pip install avidashboard-kilo.tar.gz

   If you have a previous version of avidashboard, please uninstall that
   before installing the newer version::

    pip uninstall avidashboard

3. Modify horizon's settings file to add avidashboard. If you are in a development
   environment, then this file is horizon/openstack_dashboard/settings.py. If you
   are in a production environment, most likely it is at
   /usr/share/openstack-dashboard/openstack_dashboard/settings.py

   Import enabled and update settings::

    import avidashboard.enabled    # ADD THIS LINE

    ...

    INSTALLED_APPS = list(INSTALLED_APPS)  # Make sure it's mutable
    settings.update_dashboards([
       openstack_dashboard.enabled,
       openstack_dashboard.local.enabled,
       avidashboard.enabled,      # ADD THIS LINE TOO
    ], HORIZON_CONFIG, INSTALLED_APPS)
    
    ...


   For Juno Horizon,
   also add the following in the same file::

    INSTALLED_APPS = [
       'avidashboard',  # ADD THIS LINE
       'openstack_dashboard',
       ...
    ]

4. Add the IP address(es) of the Avi Controller to your local_settings (typically in
   openstack_dashboard/local/local_settings.py in development environment, or at
   /etc/openstack_dashboard/local_settings.py in a production environment).
   For example::

    AVI_CONTROLLER = {"RegionA": "regiona.avi-lbaas.example.net",
                      "RegionB": "regionb.avi-lbaas.example.net", }

5. (Optional) Enable the Avi Analytics Tab by setting the following in your
   local settings file (Make sure clickjacking protection is not enabled on
   Avi Controller; see notes below)::

    AVI_ANALYTICS_TAB_ENABLED = True
                  
6. (Optional) Enable full LBaaS panel to be the Avi UI by setting the following in your
   local settings file (Make sure clickjacking protection is not enabled on
   Avi Controller; see notes below)::

    AVI_LBAAS_FULL_UI = True

   In Juno's version of Horizon, there was a bug in _tab_group.html template file, which causes the title of a tab to be shown in a tab group even when there is only tab in the tab group. This is fixed in later versions. To get around this issue, just rewrite _tab_group.html file with the Kilo version at https://github.com/openstack/horizon/blob/stable/kilo/horizon/templates/horizon/common/_tab_group.html.

   Location of the _tab_group.html file:
    *redhat*: /usr/lib/python2.7/site-packages/horizon/templates/horizon/common/_tab_group.html,
    *ubuntu*: /usr/lib/python2.7/dist-packages/horizon/templates/horizon/common/_tab_group.html

7. Restart horizon. For example::

    $> apache2ctl restart


Notes:
-----

Starting version 15.3, Avi Controller has clickjacking protection in place.
Unfortunately, the Horizon integration with iframes does not work with the clickjacking
protection in place. To disable this, please login to the Avi Controller and perform
the following steps::

   $> shell
   Login: admin
   Password:

   : > configure systemconfiguration
   : systemconfiguration> portal_configuration
   : systemconfiguration:portal_configuration> no enable_clickjacking_protection
   : systemconfiguration:portal_configuration> save
   : systemconfiguration> save
   : > exit
   $>
