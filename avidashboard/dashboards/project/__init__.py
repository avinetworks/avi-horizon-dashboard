# Copyright 2015 Avi Networks, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from django.conf import settings
import os

# add analytics templates
settings.TEMPLATE_DIRS += (os.path.realpath(os.path.dirname(__file__)+ "/../../templates"),)

# patch to create a new certificates tab
from openstack_dashboard.dashboards.project.loadbalancers.tabs import LoadBalancerTabs
from avidashboard.dashboards.project.loadbalancers.tabs import CertificatesTab
from avidashboard.dashboards.project.loadbalancers.tabs import AviUITab
LoadBalancerTabs.tabs += (CertificatesTab,)

if getattr(settings, "AVI_ANALYTICS_TAB_ENABLED", False):
    LoadBalancerTabs.tabs += (AviUITab,)

if getattr(settings, "AVI_LBAAS_FULL_UI", False):
    LoadBalancerTabs.tabs = (AviUITab,)

# patch to add relevant URLs
from openstack_dashboard.dashboards.project.loadbalancers.urls import urlpatterns
from avidashboard.dashboards.project.loadbalancers.urls import urlpatterns as avi_urls
urlpatterns.extend(avi_urls)

# patch to add a new row action link in the pools table
from openstack_dashboard.dashboards.project.loadbalancers.tables import PoolsTable
from avidashboard.dashboards.project.loadbalancers.tables import (
    AssociateCertificateLink, DisassociateCertificateLink)
PoolsTable._meta.row_actions += (AssociateCertificateLink, DisassociateCertificateLink)
PoolsTable.base_actions[AssociateCertificateLink.name] = AssociateCertificateLink()
PoolsTable.base_actions[DisassociateCertificateLink.name] = DisassociateCertificateLink()

# patch to modify addvip help message
from openstack_dashboard.dashboards.project.loadbalancers.workflows import AddVipAction
AddVipAction.help_text += ("\n\n\n</b>IMPORTANT: If you are configuring SSL Offload with "
                           "unencrypted HTTP to your pool members, select 'HTTP' "
                           "in the Protocol field</b>\n\n\n")

# patch to ignore SEs in addmember action (courtesy: Eric Peterson, TWC)
from openstack_dashboard.dashboards.project.loadbalancers.workflows \
    import AddMemberAction

oldAddMemberActionInit = AddMemberAction.__init__


def newAddMemberActionInit(self, request, *args, **kwargs):
    from openstack_dashboard import api
    real_svr_list = api.nova.server_list

    try:

        def filtered_nova_list(request):
            instances, more = real_svr_list(request)
            instances = [instance for instance
                         in instances
                         if 'AVICNTRL' not in instance.metadata]
            return instances, more

        api.nova.server_list = filtered_nova_list
        oldAddMemberActionInit(self, request, *args, **kwargs)
    finally:
        api.nova.server_list = real_svr_list


AddMemberAction.__init__ = newAddMemberActionInit

# patch to add cert information in pool table
from openstack_dashboard.dashboards.project.loadbalancers import tables \
    as lbtables
from avidashboard.api import avi
old_get_data = lbtables.UpdatePoolsRow.get_data


def add_pool_vip_info(pool, request):
    pool.cert = None
    if pool.vip_id:
        try:
            vip = avi.get_vip(request, pool.vip_id)
            cert = avi.get_vip_cert(vip)
            if cert:
                pool.cert = cert
            http_port = avi.get_vip_http_port(vip)
            if http_port > 0:
                pool.http_port = http_port
        except Exception as e:
            print "Error in obtaining certificate info: %s" % e
    return pool


def new_get_data(self, request, pool_id):
    pool = old_get_data(self, request, pool_id)
    return add_pool_vip_info(pool, request)


lbtables.UpdatePoolsRow.get_data = new_get_data


old_get_vip_name = lbtables.get_vip_name
from django.utils.safestring import SafeText


def get_vip_name(pool):
    ret_string = old_get_vip_name(pool)
    if hasattr(pool, "cert") and pool.cert:
        ret_string += "\n<br/>\n Certificate: %s\n" % pool.cert
        if hasattr(pool, "http_port") and pool.http_port > 0:
            ret_string += "\n<br/>\n HTTP Redirect: Port %s\n" % pool.http_port
        ret_string = SafeText(ret_string)
    return ret_string

lbtables.PoolsTable.base_columns['vip_name'].transform = get_vip_name


from openstack_dashboard.api import lbaas
old_pool_list = lbaas._pool_list


def new_pool_list(request, expand_subnet=False, expand_vip=False, **kwargs):
    plist = old_pool_list(request, expand_subnet, expand_vip, **kwargs)
    for pool in plist:
        add_pool_vip_info(pool, request)
    return plist

lbaas._pool_list = new_pool_list
