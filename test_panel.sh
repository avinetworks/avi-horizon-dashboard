set -e
set -x

HORIZON_BRANCH=${HORIZON_BRANCH:-"origin/stable/newton"}
AVI_CONTROLLER=${AVI_CONTROLLER:-"{'RegionOne': '10.10.25.201'}"}
OS_CONTROLLER=${OS_CONTROLLER:-"10.10.37.183"}
# v2 or v3
KEYSTONE_VERSION=${KEYSTONE_VERSION:-v3}
# rerun -- set it to true, when runnig second time for the same branch
# this avoids needing to download the horizon code again
RERUN=${RERUN:-false}

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
    set +e
    ./run_tests.sh --runserver 0.0.0.0:9000
    set -e
    .venv/bin/pip install --upgrade pip
fi

# config
cp openstack_dashboard/local/local_settings.py.example openstack_dashboard/local/local_settings.py
sed -i "s/\#ALLOWED_HOSTS = \['horizon.example.com', \]/ALLOWED_HOSTS = \['\*',\]/g" openstack_dashboard/local/local_settings.py
sed -i "s/OPENSTACK_HOST = \"127.0.0.1\"/OPENSTACK_HOST = \"$OS_CONTROLLER\"/g" openstack_dashboard/local/local_settings.py

.venv/bin/pip install ../dist/avidashboard*
echo "AVI_LBAAS_FULL_UI = True" >> openstack_dashboard/local/local_settings.py
echo "AVI_CONTROLLER = $AVI_CONTROLLER" >> openstack_dashboard/local/local_settings.py
echo "AVI_LBAAS_PANEL_NAME = 'Avi LB'"  >> openstack_dashboard/local/local_settings.py

if [ "$KEYSTONE_VERSION" = "v3" ]; then
    echo "OPENSTACK_KEYSTONE_MULTIDOMAIN_SUPPORT = True"  >> openstack_dashboard/local/local_settings.py
    echo "OPENSTACK_KEYSTONE_DEFAULT_DOMAIN = 'default'"  >> openstack_dashboard/local/local_settings.py
    echo "OPENSTACK_KEYSTONE_URL = \"http://%s:5000/v3\" % OPENSTACK_HOST"  >> openstack_dashboard/local/local_settings.py
    echo 'OPENSTACK_API_VERSIONS = {"identity": 3,"image": 2,"volume": 2,}' >> openstack_dashboard/local/local_settings.py
fi

# enabled via local settings
cat << EOF > ls_change
try:
    from openstack_dashboard.settings import __file__ as ods_file
    with open(os.path.dirname(os.path.realpath(ods_file)) + "/enabled/_1490_avi_lbaas.py", "w+") as f:
        f.write("""
PANEL = 'avi'
# The name of the dashboard the PANEL associated with. Required.
PANEL_DASHBOARD = 'project'
# The name of the panel group the PANEL is associated with.
PANEL_GROUP = 'network'

ADD_EXCEPTIONS = {
}

#ADD_INSTALLED_APPS = ['avidashboard.dashboards.project']
ADD_PANEL = 'avidashboard.dashboards.project.loadbalancers.panel.AviLBaaSPanel'
""")
except Exception as e:
    print "Avi Failure: %s" % e
EOF

sed -ie "14r ls_change" openstack_dashboard/local/local_settings.py

./run_tests.sh --runserver 0.0.0.0:9000
