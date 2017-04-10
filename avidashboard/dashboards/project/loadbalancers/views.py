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

from django.utils.http import urlencode
from django.conf import settings

import re
import logging
LOG = logging.getLogger(__name__)


from horizon.views import HorizonTemplateView
from avidashboard import api


class IndexView(HorizonTemplateView):
    template_name = 'project/aviloadbalancers/avi_analytics.html'
    page_title = getattr(settings, "AVI_LBAAS_PANEL_NAME", 'Load Balancers')

    def get_tenant_name(self, avisession):
        if self.request.user.tenant_name == "admin":
            return "admin"
        utl_resp = avisession.get("user-tenant-list").json()
        for t in utl_resp["tenants"]:
            if t["uuid"] == avisession.tenant_uuid:
                return t["name"]
        raise Exception("couldn't find tenant on Avi")

    def get_context_data(self, **kwargs):
        request = self.request
        controller_ip = ""
        csrf_token = ""
        session_id = ""
        try:
            avi_session = api.avi.avisession(request)
            controller_ip = avi_session.controller_ip
            csrf_token = avi_session.headers["X-CSRFToken"]
            session_id = avi_session.cookies.get("sessionid")
            tenant_name = self.get_tenant_name(avi_session)
        except Exception as e:
            LOG.warning("Couldn't create a session to Avi Controller: %s", e)
            tenant_name = ""
        other_ui_options = "permissions=USER_MENU,NO_ACCESS"
        if getattr(settings, "AVI_LBAAS_FULL_UI", False):
            other_ui_options += "&read_only=False"
        else:
            other_ui_options += ",MAIN_MENU,NO_ACCESS,HELP,NO_ACCESS&read_only=True"
        return {
            'controller_ip': controller_ip,
            'csrf_token': csrf_token,
            'session_id': session_id,
            'tenant_name': urlencode({tenant_name: ""})[:-1],
            'other_ui_options': other_ui_options,
        }
