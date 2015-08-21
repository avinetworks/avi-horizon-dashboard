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
from horizon import messages
from django.conf import settings
import os

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
        except Exception as e:
            certificates = []
            messages.warning(self.tab_group.request, _("Unable to retrieve certificates"))
            #exceptions.handle(self.tab_group.request,
            #                  _('Unable to retrieve certificates list.'))
        return certificates


class AviUITab(tabs.Tab):
    name = "Analytics"
    slug = "analytics"
    preload = False
    template_set = False

    def set_template(self):
        if self.template_set:
            return
        self.template_set = True
        fname = os.path.join(settings.TEMPLATE_DIRS[0], "avi_analytics.html")
        with open(fname, "w+") as fh:
            fh.write("<iframe src=\"https://")
            fh.write("{{ controller_ip  }}")
            fh.write("/#/authenticated/applications/dashboard?csrf_token=")
            fh.write("{{ csrf_token }}")
            fh.write("&session_id=")
            fh.write("{{ session_id }}")
            fh.write("&tenant_name=")
            fh.write("{{ tenant_name }}\"")
            fh.write("id=\"aviDashboard\" sandbox=\"allow-scripts"
                     " allow-same-origin\" width=\"100%\""
                     " height=\"600\"></iframe>\n")
        return

    def get_template_name(self, request):
        self.set_template()
        return "avi_analytics.html"

    def get_context_data(self, request, **kwargs):
        avi_session = api.avi.avisession(request)
        return {
            'controller_ip': avi_session.controller_ip,
            'csrf_token': avi_session.sess.headers["X-CSRFToken"],
            'session_id': avi_session.sess.cookies.get("sessionid"),
            'tenant_name': avi_session.tenant
        }
