===============================
avidashboard
===============================

Avi Horizon UI bits: Adds a new Panel

* Free software: Apache license

The following instructions add a new **panel** on Horizon dashboard under Project>Networks
section for showing Avi's full UI in one of the following modes: 
(i) READ-WRITE mode: users can edit all objects they have privileges to modify, or
(ii) READ-ONLY mode: users cannot make any edits to virtual services, pools, etc., but can view analytics, logs, and events.

Installation
------------

1. Obtain the avidashboard PIP package for "panel" from the releases page: https://github.com/avinetworks/avi-horizon-dashboard/releases/.
   We also distribute a Debian package for "panel" code on the same page.

2. Install the python package using the pip command as follows::

    pip install --upgrade avidashboard-panel.tar.gz

   In the above command, "--upgrade" option ensures that the newly downloaded
   version overwrites any other version of avidashboard that already exists.

3. Update your local_settings file with the following steps. This is typically
   openstack_dashboard/local/local_settings.py in development environment, or
   /etc/openstack_dashboard/local_settings.py in a production environment.

4. Add the following code into local_settings.py at the end so that
   Avi code gets imported into Horizon as well::

    # for enabling Avi Dashboard's panel
    from openstack_dashboard.utils import settings as utsettings
    import avidashboard.enabled
    orig_func = utsettings.update_dashboards

    def new_update_dashboards(modules, config, apps):
        modules.append(avidashboard.enabled)
        return orig_func(modules, config, apps)

    utsettings.update_dashboards = new_update_dashboards

   Note that there is a bug in Mitaka code, later fixed in Newton code
   (https://github.com/openstack/horizon/commit/ea92e735829ae4271fcbae932f69ffdbda268546),
   that causes Avi panel to show at the top of the list under "Network" section
   instead of at the bottom. You can either use Newton Horizon code or apply
   the fix from the commit referenced above.
    
5. Add the IP address(es) of the Avi Controller in local_settings.py.
   For example::

    AVI_CONTROLLER = {"RegionA": "regiona.avi-lbaas.example.net",
                      "RegionB": "regionb.avi-lbaas.example.net", }

6. Enable full LBaaS panel to be the Avi UI in local_settings.py.
   (Make sure clickjacking protection is not enabled on
   Avi Controller; see the notes at the end)::

    AVI_LBAAS_FULL_UI = True

   If you want Avi UI in read-only mode, then set the following
   instead of the above::

    AVI_LBAAS_FULL_READONLY_UI = True

   **NOTE**: Set only one of the above in your config file.

7. (Optional) The default name for the full LBaaS panel is "Loadbalancers". You can change it
   to a custom name by adding the following setting to local_settings.py::

    AVI_LBAAS_PANEL_NAME = "Avi Loadbalancer"

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
