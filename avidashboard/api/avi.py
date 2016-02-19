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
import json
import requests
import pytz
import datetime

from django.conf import settings


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


class AviSession():
    sess = None
    prefix = ""
    username = None
    password = None
    tenant = None
    keystone_token = None
    controller_ip = None

    def __init__(self, controller_ip, username, password=None, token=None,
                 tenant=None):
        self.sess = requests.Session()
        self.controller_ip = controller_ip
        self.username = username
        self.password = password
        self.keystone_token = token
        self.tenant = tenant

        self.prefix = "https://%s/" % controller_ip
        self.authenticate_session()
        return

    def authenticate_session(self):
        resp = self.sess.get(self.prefix, verify=False, timeout=timeout)
        self.update_csrf_token(resp)
        self.sess.headers.update({"Referer": self.prefix})
        body = {"username": self.username}
        if not self.keystone_token:
            body["password"] = self.password
        else:
            body["token"] = self.keystone_token
        json_resp = self.post("login", body,timeout=timeout, verify=False)
        if len(json_resp) <= 0:
            raise Exception("Did not get any response during authentication")
        # switch to a different tenant if needed
        if self.tenant:
            self.sess.headers.update({"X-Avi-Tenant": "%s" % self.tenant})
        self.sess.headers.update({"Content-Type": "application/json"})
        logger.info("sess headers: %s", self.sess.headers)
        return

    def update_csrf_token(self, resp):
        cookies = requests.utils.dict_from_cookiejar(resp.cookies)
        if "csrftoken" in cookies:
            self.sess.headers.update({"X-CSRFToken": cookies["csrftoken"]})
        return

    def get(self, url, *args, **kwargs):
        return self.call_api("get", self.prefix + url, *args, **kwargs)

    def post(self, url, *args, **kwargs):
        return self.call_api("post", self.prefix + url, *args, **kwargs)

    def put(self, url, *args, **kwargs):
        return self.call_api("put", self.prefix + url, *args, **kwargs)

    def delete(self, url, *args, **kwargs):
        return self.call_api("delete", self.prefix + url, *args, **kwargs)

    def call_api(self, method, *args, **kwargs):
        resp = getattr(self.sess, method)(*args, **kwargs)
        self.update_csrf_token(resp)
        if resp.status_code >= 300:
            raise AviResponseException("URL: %s (kwargs=%s)" %
                                       (args[0], kwargs), resp.status_code,
                                       resp.content)
        json_resp = []
        if len(resp.content) > 0:
            json_resp = json.loads(resp.content)
        # logger.info("URL: %s (kwargs=%s), Status: %s, Resp: %s",
        #             args[0], kwargs, resp.status_code, json_resp)
        return json_resp


avi_sessions = {}


def session_cleanup():
    for token in avi_sessions.keys():
        if token.expires < datetime.datetime.now(tz=pytz.utc):
            avi_sessions.pop(token)
    return


def avisession(request, tenant=None):
    avi_controller_cfg = getattr(settings, 'AVI_CONTROLLER', {})
    region = request.session['services_region']
    if region not in avi_controller_cfg:
        raise Exception("No Avi Controller Configured for Region %s" % region)
    controller = avi_controller_cfg[region]
    token = request.user.token
    username = request.user.username
    if not tenant:
        tenant = request.user.tenant_name
    if token in avi_sessions and tenant in avi_sessions[token]\
            and region in avi_sessions[token][tenant]:
        return avi_sessions[token][tenant][region]
    session = AviSession(controller, username=username, token=token.id,
                        tenant=tenant)
    if token not in avi_sessions:
        avi_sessions[token] = {}
    if tenant not in avi_sessions[token]:
        avi_sessions[token][tenant] = {}
    avi_sessions[token][tenant][region] = session
    # print "adding session for user %s tenant %s" % (username, tenant)
    session_cleanup()
    return session

Cert = collections.namedtuple("Cert", ["id", "name", "cname", "iname", "algo", "self_signed", "expires"])


def certs_list(request, tenant_name):
    sess = avisession(request, tenant_name)
    certs = sess.get("/api/sslkeyandcertificate?type=SSL_CERTIFICATE_TYPE_VIRTUALSERVICE")
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
    sess = avisession(request, request.user.tenant_name)
    logger.info("sess headers: %s", sess.sess.headers)
    try:
        resp = sess.post("/api/sslkeyandcertificate/importkeyandcertificate",
                     data=json.dumps({"name": kwargs["name"],
                                      "certificate": kwargs["cert_data"],
                                      "key": kwargs["key_data"],
                                      "key_passphrase": kwargs["passphrase"]}),
                     verify=False, timeout=timeout)
        print "resp: %s" % resp
    except AviResponseException as aex:
        if aex.content:
            json_resp = json.loads(aex.content)
            raise Exception(json_resp["error"])
        else:
            raise
    return {"id": resp['uuid']}


def delete_cert(request, cert_id):
    # def add_ssl_key_and_cert(sess, certname, key_str, cert_str, passphrase):
    sess = avisession(request, request.user.tenant_name)
    logger.info("sess headers: %s", sess.sess.headers)
    try:
        resp = sess.delete("/api/sslkeyandcertificate/%s" % cert_id,
                           verify=False, timeout=timeout)
        print "resp: %s" % resp
    except AviResponseException as aex:
        if aex.content:
            json_resp = json.loads(aex.content)
            raise Exception(json_resp["error"])
        else:
            raise
    return {"id": cert_id}


def get_pool_cert(request, pool_id):
    sess = avisession(request, request.user.tenant_name)
    pool_id = "pool-%s" % pool_id
    pool = sess.get("/api/pool/%s?include_name=true" % pool_id)
    if "ssl_key_and_certificate_ref" in pool:
        return pool["ssl_key_and_certificate_ref"].split("#")[1]
    return ""


def get_vip(request, vip_id):
    sess = avisession(request, request.user.tenant_name)
    vip_id = "virtualservice-%s" % vip_id
    vip = sess.get("/api/virtualservice/%s?include_name=true" % vip_id)
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
    sess = avisession(request, request.user.tenant_name)
    logger.info("sess headers: %s", sess.sess.headers)
    pool_proto = kwargs.get("pool_proto")
    pool_cert = kwargs.get("pool_cert")
    # get sslprofiles and sslcerts from avi
    certs = sess.get("/api/sslkeyandcertificate").get("results", [])
    profiles = sess.get("/api/sslprofile").get("results", [])
    def_profile = profiles[0]["url"]
    # update
    if pool_cert or pool_proto == 'HTTPS':
        upd = dict()
        pool_id = "pool-" + kwargs.get("pool_id")
        pool = sess.get("/api/pool/%s" % pool_id)
        if not pool.get('ssl_profile_ref'):
            upd["ssl_profile_ref"] = def_profile
        if pool_cert:
            cert_url = next(iter([cert["url"] for cert in certs if cert["name"] == pool_cert]), "")
            #  put pool with default sslprofile and chosen sslcert
            upd["ssl_key_and_certificate_ref"] = cert_url
        if upd:
            pool.update(upd)
            resp = sess.put("/api/pool/%s" % pool_id, data=json.dumps(pool))
            logger.debug("Pool cert update resp: %s", resp)

    # now update VIP
    if kwargs.get("vip_cert"):
        vip_id = "virtualservice-" + kwargs.get("vip_id")
        vip = sess.get("/api/virtualservice/%s" % vip_id)
        cert_url = next(iter([cert["url"] for cert in certs if cert["name"] == kwargs.get("vip_cert")]), "")
        # always set vip application_profile_ref to system secure http
        ssl_app_profile = sess.get("api/applicationprofile?name=System-Secure-HTTP").get("results")[0]["url"]
        vip["application_profile_ref"] = ssl_app_profile
        vip["ssl_profile_ref"] = def_profile
        vip["ssl_key_and_certificate_refs"] = [cert_url]
        vip["services"][0]['enable_ssl'] = True

        # check and add new listener also
        if kwargs.get("redirect_choice") == "yes":
            vip["services"].append({"port": kwargs.get("http_port")})

        resp = sess.put("/api/virtualservice/%s" % vip_id, data=json.dumps(vip))
        logger.debug("VIP cert update resp: %s", resp)
    return


def disassociate_certs(request, **kwargs):
    sess = avisession(request, request.user.tenant_name)
    logger.info("sess headers: %s", sess.sess.headers)
    pool_proto = kwargs.get("pool_proto")
    pool_cert = kwargs.get("pool_cert")
    # update
    if pool_cert or pool_proto == 'HTTPS':
        pool_id = "pool-" + kwargs.get("pool_id")
        pool = sess.get("/api/pool/%s" % pool_id)
        # remove chosen sslcert - dont remove sslprofile
        for key in ["ssl_key_and_certificate_ref"]:
            if pool.has_key(key):
                pool.pop(key)
        resp = sess.put("/api/pool/%s" % pool_id, data=json.dumps(pool))
        logger.debug("Pool cert update resp: %s", resp)
        l4profs = sess.get("/api/applicationprofile?name=System-L4-Application").get("results", [])
        def_profile = l4profs[0]["url"]
    else:
        l7profs = sess.get("/api/applicationprofile?name=System-HTTP").get("results", [])
        def_profile = l7profs[0]["url"]
    # now update VIP
    if kwargs.get("vip_cert"):
        vip_id = "virtualservice-" + kwargs.get("vip_id")
        vip = sess.get("/api/virtualservice/%s" % vip_id)
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
        resp = sess.put("/api/virtualservice/%s" % vip_id, data=json.dumps(vip))
        logger.debug("VIP cert update resp: %s", resp)
    return
