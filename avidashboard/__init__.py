# -*- coding: utf-8 -*-

# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import pbr.version

from django.conf.urls import include, url

__version__ = pbr.version.VersionInfo(
    'avidashboard').version_string()

# patch to create a new certificates tab
from openstack_dashboard.dashboards.project.loadbalancers.tabs import LoadBalancerTabs
from avidashboard.dashboards.project.loadbalancers.tabs import CertificatesTab
LoadBalancerTabs.tabs += (CertificatesTab,)

# patch to add relevant URLs
from openstack_dashboard.dashboards.project.loadbalancers.urls import urlpatterns
from avidashboard.dashboards.project.loadbalancers.urls import urlpatterns as avi_urls
urlpatterns.extend(avi_urls)

# patch to add a new row action link in the pools table
from openstack_dashboard.dashboards.project.loadbalancers.tables import PoolsTable
from avidashboard.dashboards.project.loadbalancers.tables import AssociateCertificateLink
PoolsTable._meta.row_actions += (AssociateCertificateLink,)
PoolsTable.base_actions[AssociateCertificateLink.name] = AssociateCertificateLink()
