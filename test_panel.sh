set -e
set -x

HORIZON_BRANCH=${HORIZON_BRANCH:-"origin/stable/queens"}
AVI_CONTROLLER=${AVI_CONTROLLER:-"{'RegionOne': '10.10.25.201'}"}
#OS_CONTROLLER=${OS_CONTROLLER:-"10.10.37.183"}
OS_CONTROLLER=${OS_CONTROLLER:-"10.10.33.218"} #anant pike
# v2 or v3
KEYSTONE_VERSION=${KEYSTONE_VERSION:-v3}
# rerun -- set it to true, when runnig second time for the same branch
# this avoids needing to download the horizon code again
RERUN=${RERUN:-false}
USETOX=${USETOX:-false}

# compile horizon plugin
rm -rf dist
python setup.py sdist

if [ "$RERUN" = false ]; then
    # create a horizon directory
    rm -rf horizon
    git clone https://github.com/openstack/horizon
fi

cd horizon/

if [ "$RERUN" = false ]; then
    git checkout $HORIZON_BRANCH
    if [ "$USETOX" = false ]; then
        set +e
        ./run_tests.sh --runserver 0.0.0.0:9000
        set -e
        .venv/bin/pip install --upgrade pip
    else
        TOXENV=py27dj110 tox --notest
    fi
fi

# config
cp openstack_dashboard/local/local_settings.py.example openstack_dashboard/local/local_settings.py
sed -i "s/\#ALLOWED_HOSTS = \['horizon.example.com', \]/ALLOWED_HOSTS = \['\*',\]/g" openstack_dashboard/local/local_settings.py
sed -i "s/OPENSTACK_HOST = \"127.0.0.1\"/OPENSTACK_HOST = \"$OS_CONTROLLER\"/g" openstack_dashboard/local/local_settings.py


if [ "$USETOX" = false ]; then
    .venv/bin/pip install ../dist/avidashboard*
else
    .tox/py27dj110/bin/pip install ../dist/avidashboard*
fi

echo "" >> openstack_dashboard/local/local_settings.py
echo "AVI_LBAAS_FULL_UI = True" >> openstack_dashboard/local/local_settings.py
echo "AVI_CONTROLLER = $AVI_CONTROLLER" >> openstack_dashboard/local/local_settings.py
echo "AVI_LBAAS_PANEL_NAME = 'Avi LB'"  >> openstack_dashboard/local/local_settings.py

if [ "$KEYSTONE_VERSION" = "v3" ]; then
    echo "OPENSTACK_KEYSTONE_MULTIDOMAIN_SUPPORT = True"  >> openstack_dashboard/local/local_settings.py
    echo "OPENSTACK_KEYSTONE_DEFAULT_DOMAIN = 'default'"  >> openstack_dashboard/local/local_settings.py
    echo "OPENSTACK_KEYSTONE_URL = \"http://%s:5000/v3\" % OPENSTACK_HOST"  >> openstack_dashboard/local/local_settings.py
    echo 'OPENSTACK_API_VERSIONS = {"identity": 3,"image": 2,"volume": 2,}' >> openstack_dashboard/local/local_settings.py
fi

cat << EOF >> openstack_dashboard/local/local_settings.py

# for enabling Avi Dashboard's panel
from openstack_dashboard.utils import settings as utsettings
import avidashboard.enabled
orig_func = utsettings.update_dashboards
def new_update_dashboards(modules, config, apps):
    modules.append(avidashboard.enabled)
    return orig_func(modules, config, apps)
utsettings.update_dashboards = new_update_dashboards
EOF

if [ "$USETOX" = false ]; then
    ./run_tests.sh --runserver 0.0.0.0:9000
else
    .tox/py27dj110/bin/python ./manage.py runserver 0.0.0.0:9000
fi
