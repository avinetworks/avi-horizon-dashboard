import os
import time
from setuptools import setup, find_packages

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

if os.path.exists("./VERSION"):
    with open("./VERSION", "r") as f:
        AVI_PIP_VERSION = f.readline()
else:
    ct = time.gmtime()
    date = "%d%02d%02d" % (ct.tm_year, ct.tm_mon, ct.tm_mday)
    AVI_PIP_VERSION = '17.2b' + date
    with open("./VERSION", "w+") as f:
        f.write("%s" % AVI_PIP_VERSION)

setup(
    name = 'avidashboard_panel',
    version = AVI_PIP_VERSION,
    packages = find_packages(),
    description = 'Avi Horizon Dashboard Plugin for LBaaSv1 Panel.',
    url = 'http://avinetworks.com/',
    author = 'Avi Networks',
    author_email = 'support@avinetworks.com',
    classifiers = [
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
    include_package_data=True,
    install_requires = [''],
    package_data={'avi': ['*.cfg', '*.conf', '*.crt', '*.json', '*.key',
                          '*.pem', '*.xml', '*.yaml', '*.html']},
)
