#    Copyright 2013, Big Switch Networks, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from django.core.urlresolvers import reverse
from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages
from horizon import tabs
from horizon.utils import memoized
from horizon import workflows

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.loadbalancers \
    import forms as project_forms
from openstack_dashboard.dashboards.project.loadbalancers \
    import tables as project_tables
from openstack_dashboard.dashboards.project.loadbalancers \
    import tabs as project_tabs
from openstack_dashboard.dashboards.project.loadbalancers import utils
from avidashboard.dashboards.project.loadbalancers \
    import workflows as project_workflows

import re


class AssociateCertificateView(workflows.WorkflowView):
    workflow_class = project_workflows.AssociateCertificate

    def get_initial(self):
        initial = super(AssociateCertificateView, self).get_initial()
        initial['pool_id'] = self.kwargs['pool_id']
        try:
            pool = api.lbaas.pool_get(self.request, initial['pool_id'])
            initial['vip_id'] = pool.vip_id
        except Exception as e:
            initial['vip_id'] = ''
            msg = _('Unable to retrieve pool object and vip_id. %s') % e
            exceptions.handle(self.request, msg)
        return initial


class AddCertificateView(workflows.WorkflowView):
    workflow_class = project_workflows.AddCertificate
