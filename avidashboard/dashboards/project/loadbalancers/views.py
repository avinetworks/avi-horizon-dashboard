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


from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import workflows

from openstack_dashboard import api

from avidashboard.dashboards.project.loadbalancers \
    import workflows as project_workflows

import re
import logging
LOG = logging.getLogger(__name__)


class AssociateCertificateView(workflows.WorkflowView):
    workflow_class = project_workflows.AssociateCertificate

    def get_initial(self):
        initial = super(AssociateCertificateView, self).get_initial()
        pool_id = self.kwargs['pool_id']
        try:
            pool = api.lbaas.pool_get(self.request, pool_id)
            initial['pool_id'] = pool_id if pool.protocol != 'HTTP' else None
            initial['vip_id'] = pool.vip_id
        except Exception as e:
            initial['vip_id'] = ''
            msg = _('Unable to retrieve pool object and vip_id. %s') % e
            exceptions.handle(self.request, msg)
        return initial

class DisassociateCertificateView(workflows.WorkflowView):
    workflow_class = project_workflows.DisassociateCertificate

    def get_initial(self):
        initial = super(DisassociateCertificateView, self).get_initial()
        pool_id = self.kwargs['pool_id']
        try:
            pool = api.lbaas.pool_get(self.request, pool_id)
            initial['pool_id'] = pool_id if pool.protocol != 'HTTP' else None
            initial['vip_id'] = pool.vip_id
        except Exception as e:
            initial['vip_id'] = ''
            msg = _('Unable to retrieve pool object and vip_id. %s') % e
            exceptions.handle(self.request, msg)
        return initial


class AddCertificateView(workflows.WorkflowView):
    workflow_class = project_workflows.AddCertificate
