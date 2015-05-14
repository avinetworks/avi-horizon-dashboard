#    Copyright 2015, Avi Networks, Inc.
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
from horizon import tabs

from avidashboard import api

from avidashboard.dashboards.project.loadbalancers import tables


class CertificatesTab(tabs.TableTab):
    table_classes = (tables.CertificatesTable,)
    name = _("Certificates")
    slug = "certificates"
    template_name = "horizon/common/_detail_table.html"

    def get_certificatestable_data(self):
        try:
            tenant_name = self.request.user.tenant_name
            certificates = api.avi.certs_list(self.tab_group.request, tenant_name)
        except Exception:
            certificates = []
            exceptions.handle(self.tab_group.request,
                              _('Unable to retrieve certificates list.'))
        return certificates
