===============================
Avi Plugin for OpenStack Dashboard (Horizon)
===============================

Avi Horizon UI plugin

* Free software: Apache license

READ THIS CAREFULLY BEFORE INSTALLING
-------------------------------------

**NOTE:** If you are using Neutron LBaaSv2 or plan to expose only Avi UI to
your horizon users, then please follow the INSTALLLATION instructions
at https://github.com/avinetworks/avi-horizon-dashboard/tree/panel/README.rst.

The following instructions are for enhancing multi-tabbed LBaaSv1 panel with the
following features:

1. A new tab to manage SSL certificates
2. A new tab to show Avi Analytics (in read only mode)
3. Enhancements to "Pools" tab: Ability to associate and disassociate certificates and
   ability to add an extra listening port (LBaaSv1 allows only one listening port per VIP).

Installation
------------

1. Obtain the avidashboard PIP package for "tabs" from the releases page: https://github.com/avinetworks/avi-horizon-dashboard/releases/
   We also distribute Debian packages on the releases page.

2. Install the python package using the pip command as follows::

    pip install --upgrade avidashboard-tabs.tar.gz

   If you have a previous version of avidashboard, the above command will remove it
   and install this newer version.

3. Modify horizon's settings file to add avidashboard. If you are in a development
   environment, then this file is horizon/openstack_dashboard/settings.py. If you
   are in a production environment, most likely it is at
   /usr/share/openstack-dashboard/openstack_dashboard/settings.py

   Import enabled and update settings (only add the lines commented with "ADD THIS LINE")::

    import avidashboard.enabled    # ADD THIS LINE

    ...

    INSTALLED_APPS = list(INSTALLED_APPS)  # Make sure it's mutable
    settings.update_dashboards([
       openstack_dashboard.enabled,
       openstack_dashboard.local.enabled,
       avidashboard.enabled,      # ADD THIS LINE TOO
    ], HORIZON_CONFIG, INSTALLED_APPS)
    
    ...


   For *Juno Horizon*,
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

   Note that this option is only applicable for LBaaS v1.0 multi-tabbed panel.
   Make sure that the LBaaS is enabled in local_settings.py: the variable enable_lb
   should be set to True.
                  
6. (Optional) Enable full LBaaS panel to be the Avi UI by setting the following in your
   local settings file (Make sure clickjacking protection is not enabled on
   Avi Controller; see notes below)::

    AVI_LBAAS_FULL_UI = True

   If you want Avi UI in read-only mode, then set the following
   instead of the above::

    AVI_LBAAS_FULL_READONLY_UI = True

   In *Juno's* version of Horizon, there was a bug in _tab_group.html template file, which causes the title of a tab to be shown in a tab group even when there is only tab in the tab group. This is fixed in later versions. To get around this issue, just rewrite _tab_group.html file with the Kilo version at https://github.com/openstack/horizon/blob/stable/kilo/horizon/templates/horizon/common/_tab_group.html.

   Location of the _tab_group.html file:
    *redhat*: /usr/lib/python2.7/site-packages/horizon/templates/horizon/common/_tab_group.html,
    *ubuntu*: /usr/lib/python2.7/dist-packages/horizon/templates/horizon/common/_tab_group.html

7. Restart horizon. For example::

    $> apache2ctl restart

8. Make sure that the Avi Controller is installed with a properly signed certificate. Please
   refer to the following KB on how to set that up: https://kb.avinetworks.com/docs/17.1/access-settings-for-clients-of-the-avi-controller/

   Note that if the Avi Controller is not installed with a properly signed certificate, then many
   browsers just show a blank page when Avi's iframe panel is opened in Horizon dashboard. As a
   temporary workaround, you can open another browser tab and access the Avi Controller's URL
   (https://<avi-controller-ip>/), and accept the self-signed certificate presented by the
   Avi Controller. After that, please refresh the Horizon tab, and the Avi iframe will start
   rendering properly.


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
