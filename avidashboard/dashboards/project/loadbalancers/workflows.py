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

import logging

from django.utils.translation import ugettext_lazy as _

from django.utils.text import normalize_newlines  # noqa

from horizon import exceptions
from horizon import forms
from horizon import workflows
from horizon import messages

from avidashboard import api


LOG = logging.getLogger(__name__)


class AddCertificateAction(workflows.Action):
    multipart = True
    name = forms.CharField(max_length=255, label=_("Name"))

    key_source_choices = [('', _('Select Key Source')),
                      ('raw', _('Direct Input')),
                      ('file', _('File'))]

    attributes = {'class': 'switchable', 'data-slug': 'keysource'}
    key_source = forms.ChoiceField(label=_('Key Source'),
                                      choices=key_source_choices,
                                      widget=forms.Select(attrs=attributes),
                                      required=True)

    script_help = _("A script or set of commands to be executed after the "
                    "instance has been built (max 16kb).")

    key_upload = forms.FileField(
        label=_('Key File'),
        help_text=script_help,
        widget=forms.FileInput(attrs={
            'class': 'switched',
            'data-switch-on': 'keysource',
            'data-keysource-file': _('Key File')}),
        required=False)

    key_data = forms.CharField(
        label=_('Key Data'),
        help_text=script_help,
        widget=forms.widgets.Textarea(attrs={
            'class': 'switched',
            'data-switch-on': 'keysource',
            'data-keysource-raw': _('Key Data')}),
        required=False)

    passphrase = forms.CharField(max_length=255,
                                 widget=forms.PasswordInput(),
                                 label=_("Key Passphrase"),
                                 required=False)
    attributes = {'class': 'switchable', 'data-slug': 'certsource'}
    cert_source = forms.ChoiceField(label=_('Cert Source'),
                                      choices=key_source_choices,
                                      widget=forms.Select(attrs=attributes),
                                      required=True)

    script_help = _("A script or set of commands to be executed after the "
                    "instance has been built (max 16kb).")

    cert_upload = forms.FileField(
        label=_('Cert File'),
        help_text=script_help,
        widget=forms.FileInput(attrs={
            'class': 'switched',
            'data-switch-on': 'certsource',
            'data-certsource-file': _('Cert File')}),
        required=False)

    cert_data = forms.CharField(
        label=_('Cert Data'),
        help_text=script_help,
        widget=forms.widgets.Textarea(attrs={
            'class': 'switched',
            'data-switch-on': 'certsource',
            'data-certsource-raw': _('Cert Data')}),
        required=False)

    def __init__(self, request, *args, **kwargs):
        super(AddCertificateAction, self).__init__(request, *args, **kwargs)

    def clean(self):
        cleaned_data = super(AddCertificateAction, self).clean()
        files = self.request.FILES
        LOG.info("In cleanup files %s cleaned_date %s", files, cleaned_data)
        key = self.clean_uploaded_files('key', files)
        LOG.info("key: %s", key)
        if key is not None:
            cleaned_data['key_data'] = key
        cert = self.clean_uploaded_files('cert', files)
        LOG.info("cert: %s", cert)
        if cert is not None:
            cleaned_data['cert_data'] = cert
        return cleaned_data

    def clean_uploaded_files(self, prefix, files):
        upload_str = prefix + "_upload"

        has_upload = upload_str in files
        if has_upload:
            upload_file = files[upload_str]
            log_script_name = upload_file.name
            LOG.info('got upload %s' % log_script_name)

            if upload_file._size > 16 * 1024:  # 16kb
                msg = _('File exceeds maximum size (16kb)')
                raise forms.ValidationError(msg)
            else:
                script = upload_file.read()
                LOG.info("script: %s", script)
                if script != "":
                    try:
                        normalize_newlines(script)
                    except Exception as e:
                        msg = _('There was a problem parsing the'
                                ' %(prefix)s: %(error)s')
                        msg = msg % {'prefix': prefix, 'error': e}
                        raise forms.ValidationError(msg)
                return script
        else:
            return None

    class Meta(object):
        name = _("Add New Certificate")
        permissions = ('openstack.services.network',)
        help_text = _("Upload a Certificate.\n\n"
                      "Specify key and certificate files to upload")


class AddCertificateStep(workflows.Step):
    action_class = AddCertificateAction
    contributes = ("name", "key_data", "passphrase", "cert_data")

    def contribute(self, data, context):
        context = super(AddCertificateStep, self).contribute(data, context)
        if data:
            return context


class AddCertificate(workflows.Workflow):
    multipart = True
    slug = "addcertificate"
    name = _("Add Certificate")
    finalize_button_name = _("Add")
    success_message = _('Added certificate')
    failure_message = _('Unable to add certificate')
    success_url = "horizon:project:loadbalancers:index"
    default_steps = (AddCertificateStep,)

    def handle(self, request, context):
        try:
            context['certificate_id'] = api.avi.add_cert(
                request, **context).get('id')
            return True
        except Exception as e:
            messages.warning(request, _("Unable to add certificate: %s" % e))
            #exceptions.handle(request, _("Unable to add certificate."))
        return False


class AssociateCertificateAction(workflows.Action):
    vip_cert = forms.ChoiceField(label=_("VIP Certificate"))
    pool_cert = forms.ChoiceField(label=_("Pool Certificate"), required=False)
    pool_proto = forms.CharField(widget=forms.HiddenInput())

    def __init__(self, request, *args, **kwargs):
        #print "request %s args %s kwargs %s" % (request, args, kwargs)
        super(AssociateCertificateAction, self).__init__(request, *args, **kwargs)
        certs = api.avi.certs_list(request, request.user.tenant_name)
        pool_cert_choices = [("", _("Select a Certificate"))]
        [pool_cert_choices.append((cert.name, cert.name)) for cert in certs]
        if args[0].has_key('pool_id') and args[0]['pool_id']:
            self.fields["pool_cert"].choices = pool_cert_choices
            self.fields["pool_cert"].initial = api.avi.get_pool_cert(request, args[0]["pool_id"])
        else:
            del self.fields["pool_cert"]
        self.fields["vip_cert"].choices = pool_cert_choices
        self.fields["vip_cert"].initial = api.avi.get_vip_cert(request, args[0]["vip_id"])
        self.fields["pool_proto"].initial = args[0]["pool_proto"]
        return

    def clean(self):
        cleaned_data = super(AssociateCertificateAction, self).clean()
        return cleaned_data

    class Meta(object):
        name = _("Associate Certificates")
        permissions = ('openstack.services.network',)
        help_text = _("Associate certificates.\n\n"
                      "Specify certificates to associate")


class AssociateCertificateStep(workflows.Step):
    action_class = AssociateCertificateAction
    contributes = ("pool_cert", "vip_cert", "pool_proto")
    depends_on = ("pool_id", "vip_id", "pool_proto")

    def contribute(self, data, context):
        context = super(AssociateCertificateStep, self).contribute(data, context)
        if data:
            return context


class AssociateCertificate(workflows.Workflow):
    slug = "associatecertificate"
    name = _("Associate Certificates")
    finalize_button_name = _("Associate")
    success_message = _('Associated certificates')
    failure_message = _('Unable to associate certificates')
    success_url = "horizon:project:loadbalancers:index"
    default_steps = (AssociateCertificateStep,)

    def handle(self, request, context):
        try:
            api.avi.associate_certs(request, **context)
            return True
        except Exception:
            exceptions.handle(request, _("Unable to associate certificates."))
        return False

class DisassociateCertificateAction(workflows.Action):
    vip_cert = forms.ChoiceField(label=_("VIP Certificate"))
    pool_cert = forms.ChoiceField(label=_("Pool Certificate"), required=False)
    pool_proto = forms.CharField(widget=forms.HiddenInput())

    def __init__(self, request, *args, **kwargs):
        #print "request %s args %s kwargs %s" % (request, args, kwargs)
        super(DisassociateCertificateAction, self).__init__(request, *args, **kwargs)
        pcert = None
        if args[0].has_key('pool_id') and args[0]['pool_id']:
            pcert = api.avi.get_pool_cert(request, args[0]["pool_id"])
            if pcert:
                self.fields["pool_cert"].choices = [(pcert, pcert)]
                self.fields["pool_cert"].initial = pcert
        if not pcert:
            del self.fields["pool_cert"]
        vcert = api.avi.get_vip_cert(request, args[0]["vip_id"])
        self.fields["vip_cert"].choices = [(vcert, vcert)]
        self.fields["vip_cert"].initial = vcert
        self.fields["pool_proto"].initial = args[0]["pool_proto"]
        return

    def clean(self):
        cleaned_data = super(DisassociateCertificateAction, self).clean()
        return cleaned_data

    class Meta(object):
        name = _("Disassociate Certificates")
        permissions = ('openstack.services.network',)
        help_text = _("Disassociate certificates.\n\n"
                      "Specify certificates to disassociate")


class DisassociateCertificateStep(workflows.Step):
    action_class = DisassociateCertificateAction
    contributes = ("pool_cert", "vip_cert", "pool_proto")
    depends_on = ("pool_id", "vip_id", "pool_proto")

    def contribute(self, data, context):
        context = super(DisassociateCertificateStep, self).contribute(data, context)
        if data:
            return context


class DisassociateCertificate(workflows.Workflow):
    slug = "disassociatecertificate"
    name = _("Disassociate Certificates")
    finalize_button_name = _("Disassociate")
    success_message = _('Disassociated certificates')
    failure_message = _('Unable to disassociate certificates')
    success_url = "horizon:project:loadbalancers:index"
    default_steps = (DisassociateCertificateStep,)

    def handle(self, request, context):
        try:
            api.avi.disassociate_certs(request, **context)
            return True
        except Exception:
            exceptions.handle(request, _("Unable to disassociate certificates."))
        return False

