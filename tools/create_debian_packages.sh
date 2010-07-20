#!/bin/sh

DEB_DIRPATH="$PWD/deb"
SCRIPT_DIRPATH=$(dirname $0)

SETUP_PY_LIST="
$SCRIPT_DIRPATH/setup.py.d/core.py
$SCRIPT_DIRPATH/setup.py.d/core-qt.py
$SCRIPT_DIRPATH/setup.py.d/core-webkit-formatter.py

$SCRIPT_DIRPATH/setup.py.d/backends-bank.py
$SCRIPT_DIRPATH/setup.py.d/backends-dating.py
$SCRIPT_DIRPATH/setup.py.d/backends-messages.py
$SCRIPT_DIRPATH/setup.py.d/backends-torrent.py
$SCRIPT_DIRPATH/setup.py.d/backends-travel.py
$SCRIPT_DIRPATH/setup.py.d/backends-video.py
$SCRIPT_DIRPATH/setup.py.d/backends-video-nsfw.py
$SCRIPT_DIRPATH/setup.py.d/backends-weather.py

$SCRIPT_DIRPATH/setup.py.d/boobank.py
$SCRIPT_DIRPATH/setup.py.d/havesex.py
$SCRIPT_DIRPATH/setup.py.d/masstransit.py
$SCRIPT_DIRPATH/setup.py.d/monboob.py
$SCRIPT_DIRPATH/setup.py.d/qboobmsg.py
$SCRIPT_DIRPATH/setup.py.d/qhavesex.py
$SCRIPT_DIRPATH/setup.py.d/qvideoob.py
$SCRIPT_DIRPATH/setup.py.d/qweboobcfg.py
$SCRIPT_DIRPATH/setup.py.d/travel.py
$SCRIPT_DIRPATH/setup.py.d/videoob.py
$SCRIPT_DIRPATH/setup.py.d/videoob_web.py
$SCRIPT_DIRPATH/setup.py.d/weboorrents.py
$SCRIPT_DIRPATH/setup.py.d/wetboobs.py
"

rm -rf $DEB_DIRPATH
mkdir $DEB_DIRPATH

for f in $SETUP_PY_LIST
do
    echo "========== Creating Debian package for $f"
    rm -rf dist
    python $f sdist
    pushd dist
    TARGZ=$(ls *.tar.gz)
    tar xf $TARGZ
    PKGNAME=$(basename $f .py)
    mkdir $DEB_DIRPATH/$PKGNAME
    TARGZ_DIRPATH=$(basename $TARGZ .tar.gz)
    pushd $TARGZ_DIRPATH
    ln -s ../../$f setup.py
    python setup.py --command-packages=stdeb.command sdist_dsc --extra-cfg-file $SCRIPT_DIRPATH/stdeb.d/$PKGNAME.cfg
    pushd deb_dist
    pushd $TARGZ_DIRPATH
    fakeroot dpkg-buildpackage
    popd
    mv *.deb *.diff.gz *.changes *.orig.tar.gz $DEB_DIRPATH/$PKGNAME/
    popd
    popd
    #break
done
