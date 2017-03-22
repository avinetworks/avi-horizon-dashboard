from django.conf import settings
from django.utils.translation import ugettext_lazy as _

import horizon


class AviLBaaSPanel(horizon.Panel):
    name = _(getattr(settings, 'AVI_LBAAS_PANEL_NAME', "Load Balancers"))
    slug = 'aviloadbalancers'
    permissions = ('openstack.services.network',)

    @staticmethod
    def can_register():
        # network_config = getattr(settings, 'OPENSTACK_NEUTRON_NETWORK', {})
        full_ui = getattr(settings, 'AVI_LBAAS_FULL_UI', False)
        readonly_ui = getattr(settings, 'AVI_LBAAS_FULL_READONLY_UI', False)
        # return network_config.get('enable_lb', True) and full_ui
        return full_ui or readonly_ui

