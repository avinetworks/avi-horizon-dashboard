#!/bin/bash
set -x
assets=""
git tag -d latest
git tag latest
git push -f origin latest
set -e
for BRANCH in juno kilo master
do
    git checkout $BRANCH
    rm -rf dist/
    python setup.py sdist
    mv dist/*tar.gz avidashboard-$BRANCH.tar.gz
    assets="$assets -a avidashboard-$BRANCH.tar.gz#pip-package-$BRANCH"
done
/root/bin/hub release edit $assets -F ReleaseNote latest
