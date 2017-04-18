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

1. Obtain the avidashboard PIP package for newton version of horizon from the
   `releases page`_.
.. _releases page: https://github.com/avinetworks/avi-horizon-dashboard/releases/tag/latest

2. Install the python package using the pip command as follows::

    pip install --upgrade avidashboard-newton.tar.gz

   In the above command, "--upgrade" option ensures that the newly downloaded
   version overwrites any other version of avidashboard that already exists.

3. Update your local_settings file with the following steps. This is typically
   openstack_dashboard/local/local_settings.py in development environment, or
   /etc/openstack_dashboard/local_settings.py in a production environment.

4. Add the following code to create a file in "enabled" directory so that
   Avi code gets imported into Horizon as well::
    
    try:
        from openstack_dashboard.settings import __file__ as ods_file
        with open(os.path.dirname(os.path.realpath(ods_file)) + "/enabled/_1490_avi_lbaas.py", "w+") as f:
            f.write("""
    PANEL = 'avi'
    PANEL_DASHBOARD = 'project'
    PANEL_GROUP = 'network'
    ADD_EXCEPTIONS = {}
    ADD_PANEL = 'avidashboard.dashboards.project.loadbalancers.panel.AviLBaaSPanel'
    """)
    except Exception as e:
        print "Avi Failure: %s" % e

5. Add the IP address(es) of the Avi Controller.
   For example::

    AVI_CONTROLLER = {"RegionA": "regiona.avi-lbaas.example.net",
                      "RegionB": "regionb.avi-lbaas.example.net", }

6. (Optional) Enable full LBaaS panel to be the Avi UI. 
   (Make sure clickjacking protection is not enabled on
   Avi Controller; see the notes at the end)::

    AVI_LBAAS_FULL_UI = True

   If you want Avi UI in read-only mode, then set the following
   instead of the above::

    AVI_LBAAS_FULL_READONLY_UI = True

7. (Optional) The default name for the full LBaaS panel is "Loadbalancers". You can change it
   to a custom name using the following setting::

    AVI_LBAAS_PANEL_NAME = "Avi Loadbalancer"

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
