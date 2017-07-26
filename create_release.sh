#!/bin/bash
set -x
assets=""
git tag -d latest
git tag latest
git push -f origin latest
set -e
for BRANCH in tabs panel
do
    rm -rf VERSION
    git checkout $BRANCH
    git pull --rebase origin $BRANCH
    rm -rf dist/ debian/ build/ ../*avidashboard*deb
    python setup.py sdist
    fname=`ls dist`
    mv dist/$fname ./
    assets="$assets -a $fname#pip-package-$BRANCH"

    # debian package
    python setup.py --command-packages=stdeb.command debianize
    dpkg-buildpackage -b -us -uc -d
    fname=`cd .. && ls *avidashboard*deb`
    assets="$assets -a $fname#debian-package-$BRANCH"
    rm -rf debian/ build/ ../*avidashboard*changes
    cp ../$fname ./
done
git checkout master
echo "$assets"
/root/utils/hub release delete latest
/root/utils/hub release create $assets -F ReleaseNote latest
