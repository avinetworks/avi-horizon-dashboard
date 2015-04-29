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

# patch to create a new certificates tab
from openstack_dashboard.dashboards.project.loadbalancers.tabs import LoadBalancerTabs
from avidashboard.dashboards.project.loadbalancers.tabs import CertificatesTab
LoadBalancerTabs.tabs += (CertificatesTab,)

# patch to add relevant URLs
from openstack_dashboard.dashboards.project.loadbalancers.urls import urlpatterns
from avidashboard.dashboards.project.loadbalancers.urls import urlpatterns as avi_urls
urlpatterns.extend(avi_urls)

# patch to add a new row action link in the pools table
from openstack_dashboard.dashboards.project.loadbalancers.tables import PoolsTable
from avidashboard.dashboards.project.loadbalancers.tables import AssociateCertificateLink
PoolsTable._meta.row_actions += (AssociateCertificateLink,)
PoolsTable.base_actions[AssociateCertificateLink.name] = AssociateCertificateLink()

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
    m = re.search('.delete([a-z]+)', action).group(1)
    if obj_ids == []:
        obj_ids.append(re.search('([0-9a-z-]+)$', action).group(1))
    if m == "certificate":
        for obj_id in obj_ids:
            try:
                api.avi.delete_cert(request, obj_id)
                messages.success(request, _('Deleted certificate %s') % obj_id)
            except Exception as e:
                exceptions.handle(request,
                                  _('Unable to delete certificate. %s') % e)

    return prev_post(self, request, *args, **kwargs)

IndexView.post = new_post
