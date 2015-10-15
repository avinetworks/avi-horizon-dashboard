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
from openstack_dashboard.dashboards.project.loadbalancers.panel import \
    LoadBalancer as LoadBalancerPanel
from avidashboard.dashboards.project.loadbalancers.tabs import CertificatesTab
from avidashboard.dashboards.project.loadbalancers.tabs import AviUITab
LoadBalancerTabs.tabs += (CertificatesTab,)

if getattr(settings, "AVI_ANALYTICS_TAB_ENABLED", False):
    LoadBalancerTabs.tabs += (AviUITab,)

if getattr(settings, "AVI_LBAAS_FULL_UI", False):
    LoadBalancerTabs.tabs = (AviUITab,)
    # if the full ui is present, we want to make sure the panel shows up
    LoadBalancerPanel.allowed = lambda x, y: True

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

# patch to intercept delete-certificate call
from openstack_dashboard.dashboards.project.loadbalancers.views import IndexView
import re
import avidashboard.api as api
from django.utils.translation import ugettext_lazy as _
from horizon import exceptions
from horizon import messages

prev_post = IndexView.post


def new_post(self, request, *args, **kwargs):
    obj_ids = request.POST.getlist('object_ids')
    action = request.POST['action']
    results = re.search('.delete([a-z]+)', action)
    if not results:
        return super(IndexView, self).post(request, *args, **kwargs)
    m = results.group(1)
    if obj_ids == []:
        obj_ids.append(re.search('([0-9a-z-]+)$', action).group(1))
    if m == "certificate":
        for obj_id in obj_ids:
            try:
                api.avi.delete_cert(request, obj_id)
                messages.success(request, _('Deleted certificate %s') % obj_id)
            except Exception as e:
                messages.error(request,
                                  _('Unable to delete certificate. %s') % e)

    return prev_post(self, request, *args, **kwargs)

IndexView.post = new_post

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
