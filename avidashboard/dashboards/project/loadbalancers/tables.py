#    Copyright 2013, Avi Networks, Inc.
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
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

from horizon import tables

from openstack_dashboard import api
from openstack_dashboard import policy


class AddCertificateLink(tables.LinkAction):
    name = "addcertificate"
    verbose_name = _("Add Certificate")
    url = "horizon:project:loadbalancers:addcertificate"
    classes = ("ajax-modal",)
    icon = "plus"
    policy_rules = (("network", "create_health_monitor"),)


class DeleteCertificateLink(policy.PolicyTargetMixin,
                        tables.DeleteAction):
    name = "deletecertificate"
    policy_rules = (("network", "delete_health_monitor"),)

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Certificate",
            u"Delete Certificates",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Scheduled deletion of Certificate",
            u"Scheduled deletion of Certificates",
            count
        )


class AssociateCertificateLink(tables.LinkAction):
    name = "associatecertificate"
    verbose_name = _("Associate Certificates")
    classes = ("ajax-modal", "btn-update")
    policy_rules = (("network", "update_vip"),)

    def get_link_url(self, pool):
        base_url = reverse("horizon:project:loadbalancers:associatecertificate",
                           kwargs={'pool_id': pool.id})
        return base_url

    def allowed(self, request, datum=None):
        if datum and datum.vip_id:
            vip = api.lbaas.vip_get(request, datum.vip_id)
        if datum and not datum.vip_id:
            return False
        if datum.protocol not in ["HTTPS", "HTTP"]:
            return False
        if vip.protocol not in ["HTTPS", "HTTP"]:
            return False
        # pool+vip proto is HTTP or HTTPS
        return True


class CertificatesTable(tables.DataTable):
    name = tables.Column("name",
                         verbose_name=_("Name"),
                         link="horizon:project:loadbalancers:certdetails")
    cname = tables.Column("cname", verbose_name=_("Common Name"))
    iname = tables.Column("iname", verbose_name=_("Issuer Name"))
    algo = tables.Column("algo", verbose_name=_("Algorithm"))
    self_signed = tables.Column("self_signed", verbose_name=_("Self Signed"))
    expires = tables.Column("expires", verbose_name=_("Valid Until"))

    class Meta(object):
        name = "certificatestable"
        verbose_name = _("Certificates")
        table_actions = (AddCertificateLink, DeleteCertificateLink)
        row_actions = ()
