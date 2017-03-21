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
from django.utils.http import urlencode
import os
import shutil

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

    def get_template_name(self, request):
        return "avi_analytics.html"

    def get_tenant_name(self, avisession):
        if self.request.user.tenant_name == "admin":
            return "admin"
        utl_resp = avisession.get("user-tenant-list").json()
        for t in utl_resp["tenants"]:
            if t["uuid"] == avisession.tenant_uuid:
                return t["name"]
        raise Exception("couldn't find tenant on Avi")

    def get_context_data(self, request, **kwargs):
        avi_session = api.avi.avisession(request)
        tenant_name = self.get_tenant_name(avi_session)
        other_ui_options = "permissions=USER_MENU,NO_ACCESS"
        if getattr(settings, "AVI_LBAAS_FULL_UI", False):
            other_ui_options += "&read_only=False"
        else:
            other_ui_options += ",MAIN_MENU,NO_ACCESS,HELP,NO_ACCESS&read_only=True"
        return {
            'controller_ip': avi_session.controller_ip,
            'csrf_token': avi_session.headers["X-CSRFToken"],
            'session_id': avi_session.cookies.get("sessionid"),
            'tenant_name': urlencode({tenant_name: ""})[:-1],
            'other_ui_options': other_ui_options,
        }

