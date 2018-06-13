# Copyright 2015 Avi Networks Inc.
# All Rights Reserved.
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

from __future__ import absolute_import

import collections
import logging
import uuid

from django.conf import settings
from avidashboard.api.avi_api import ApiSession
from openstack_dashboard.api import base as openstack_api_base
from urlparse import urlparse


logger = logging.getLogger(__name__)
timeout = 60


class AviResponseException(Exception):
    def __init__(self, err_str, resp_code, content):
        self.err_str = err_str
        self.resp_code = resp_code
        self.content = content

    def __str__(self):
        return "Response code: %s; Content: %s; %s" % (self.resp_code,
                                                       self.content,
                                                       self.err_str)


def os2avi_uuid(obj_type, eid):
    uid = str(uuid.UUID(eid))
    return obj_type + "-" + uid


def avisession(request):
    region = request.session['services_region']
    controller = get_controller_url(request, region=region)
    controller_port = None

    if controller:
        if controller.startswith('http'):
            avi_endpoint = urlparse(controller)
            controller = avi_endpoint.hostname

            if hasattr(avi_endpoint, 'port'):
                controller_port = avi_endpoint.port
    else:
        raise Exception("No Avi controller configured for region %s" % region)

    token = request.user.token
    username = request.user.username
    if(hasattr(request.user, 'user_domain_name') and
       request.user.user_domain_name and
       request.user.user_domain_name != 'Default'):
        username += "@%s" % request.user.user_domain_name
    tenant_uuid = os2avi_uuid("tenant", request.user.tenant_id)
    session = ApiSession(controller_ip=controller, username=username,
                         token=token.id, tenant_uuid=tenant_uuid,
                         port=controller_port)
    return session

Cert = collections.namedtuple("Cert", ["id", "name", "cname", "iname", "algo", "self_signed", "expires"])


def certs_list(request, tenant_name):
    sess = avisession(request)
    certs = sess.get("/api/sslkeyandcertificate?type=SSL_CERTIFICATE_TYPE_VIRTUALSERVICE").json()
    certificates = []
    for cert in certs.get('results', []):
        certificates.append(Cert(id=cert["uuid"],
                                 name=cert["name"],
                                 cname=cert["certificate"].get("subject", {}).get("common_name", ""),
                                 iname=cert["certificate"].get("issuer", {}).get("organization", ""),
                                 algo=cert["certificate"].get("signature_algorithm", ""),
                                 self_signed=(cert["certificate"].get("issuer", {}).get("organization", "") ==
                                             cert["certificate"].get("subject", {}).get("organization", "")),
                                 expires=cert["certificate"]["not_after"]))
    return certificates


def add_cert(request, **kwargs):
    # def add_ssl_key_and_cert(sess, certname, key_str, cert_str, passphrase):
    sess = avisession(request)
    resp = sess.post("/api/sslkeyandcertificate/importkeyandcertificate",
                     data={"name": kwargs["name"],
                           "certificate": kwargs["cert_data"],
                           "key": kwargs["key_data"],
                           "key_passphrase": kwargs["passphrase"]},
                     verify=False, timeout=timeout).json()

    return {"id": resp['uuid']}


def delete_cert(request, cert_id):
    # def add_ssl_key_and_cert(sess, certname, key_str, cert_str, passphrase):
    sess = avisession(request)
    resp = sess.delete("/api/sslkeyandcertificate/%s" % cert_id,
                       verify=False, timeout=timeout).json()
    print "resp: %s" % resp
    return {"id": cert_id}


def get_pool_cert(request, pool_id):
    sess = avisession(request)
    pool_id = "pool-%s" % pool_id
    pool = sess.get("/api/pool/%s?include_name=true" % pool_id).json()
    if "ssl_key_and_certificate_ref" in pool:
        return pool["ssl_key_and_certificate_ref"].split("#")[1]
    return ""


def get_controller_url(request, region=None, endpoint_type=None):
    """Find and return Avi controller URL."""
    if not region:
        region = request.user.services_region

    avi_controller_cfg = getattr(settings, 'AVI_CONTROLLER', {})
    controller = None

    if region in avi_controller_cfg:
        controller = avi_controller_cfg[region]
    else:
        try:
            # Query Keystone for avi-lbaas URL
            controller = openstack_api_base.url_for(
                request=request, service_type='avi-lbaas', region=region,
                endpoint_type=endpoint_type)
        except Exception as exp:
            pass

    return controller


def get_vip(request, vip_id):
    sess = avisession(request)
    vip_id = "virtualservice-%s" % vip_id
    vip = sess.get("/api/virtualservice/%s?include_name=true" % vip_id).json()
    return vip


def get_vip_cert(vip):
    if ("ssl_key_and_certificate_refs" in vip and
            vip["ssl_key_and_certificate_refs"]):
        return vip["ssl_key_and_certificate_refs"][0].split("#")[1]
    return ""


def get_vip_http_port(vip):
    for svc in vip.get("services", []):
        if not svc["enable_ssl"]:
            return svc["port"]
    return 0


def associate_certs(request, **kwargs):
    sess = avisession(request)
    pool_proto = kwargs.get("pool_proto")
    pool_cert = kwargs.get("pool_cert")
    # get sslprofiles and sslcerts from avi
    certs = sess.get("/api/sslkeyandcertificate").json().get("results", [])
    profiles = sess.get("/api/sslprofile").json().get("results", [])
    def_profile = profiles[0]["url"]
    # update
    if pool_cert or pool_proto == 'HTTPS':
        upd = dict()
        pool_id = "pool-" + kwargs.get("pool_id")
        pool = sess.get("/api/pool/%s" % pool_id).json()
        if not pool.get('ssl_profile_ref'):
            upd["ssl_profile_ref"] = def_profile
        if pool_cert:
            cert_url = next(iter([cert["url"] for cert in certs if cert["name"] == pool_cert]), "")
            #  put pool with default sslprofile and chosen sslcert
            upd["ssl_key_and_certificate_ref"] = cert_url
        if upd:
            pool.update(upd)
            resp = sess.put("/api/pool/%s" % pool_id, data=pool).json()
            logger.debug("Pool cert update resp: %s", resp)

    # now update VIP
    if kwargs.get("vip_cert"):
        vip_id = "virtualservice-" + kwargs.get("vip_id")
        vip = sess.get("/api/virtualservice/%s" % vip_id).json()
        cert_url = next(iter([cert["url"] for cert in certs if cert["name"] == kwargs.get("vip_cert")]), "")
        # always set vip application_profile_ref to system secure http
        ssl_app_profile = sess.get("api/applicationprofile?name=System-Secure-HTTP").json().get("results")[0]["url"]
        vip["application_profile_ref"] = ssl_app_profile
        vip["ssl_profile_ref"] = def_profile
        vip["ssl_key_and_certificate_refs"] = [cert_url]
        vip["services"][0]['enable_ssl'] = True

        # check and add new listener also
        if kwargs.get("redirect_choice") == "yes":
            vip["services"].append({"port": kwargs.get("http_port")})

        resp = sess.put("/api/virtualservice/%s" % vip_id, data=vip).json()
        logger.debug("VIP cert update resp: %s", resp)
    return


def disassociate_certs(request, **kwargs):
    sess = avisession(request)
    pool_proto = kwargs.get("pool_proto")
    pool_cert = kwargs.get("pool_cert")
    # update
    if pool_cert or pool_proto == 'HTTPS':
        pool_id = "pool-" + kwargs.get("pool_id")
        pool = sess.get("/api/pool/%s" % pool_id).json()
        # remove chosen sslcert - dont remove sslprofile
        for key in ["ssl_key_and_certificate_ref"]:
            if pool.has_key(key):
                pool.pop(key)
        resp = sess.put("/api/pool/%s" % pool_id, data=pool).json()
        logger.debug("Pool cert update resp: %s", resp)
        l4profs = sess.get("/api/applicationprofile?name=System-L4-Application").json().get("results", [])
        def_profile = l4profs[0]["url"]
    else:
        l7profs = sess.get("/api/applicationprofile?name=System-HTTP").json().get("results", [])
        def_profile = l7profs[0]["url"]
    # now update VIP
    if kwargs.get("vip_cert"):
        vip_id = "virtualservice-" + kwargs.get("vip_id")
        vip = sess.get("/api/virtualservice/%s" % vip_id).json()
        # always set vip application_profile_ref to system secure http
        vip["application_profile_ref"] = def_profile
        for key in ["ssl_profile_ref", "ssl_key_and_certificate_refs"]:
            if vip.has_key(key):
                vip.pop(key)
        # remove non-ssl listeners and change current ssl listener to False
        nsvcs = []
        for svc in vip['services']:
            if svc["enable_ssl"]:
                nsvcs.append(svc)
                svc['enable_ssl'] = False
        vip["services"] = nsvcs
        resp = sess.put("/api/virtualservice/%s" % vip_id, data=vip).json()
        logger.debug("VIP cert update resp: %s", resp)
    return
