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
