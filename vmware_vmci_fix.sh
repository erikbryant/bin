#!/bin/bash

PATCH_DIR=`echo $0 | sed s:[^/]*$::1`

pushd lib/modules/source
if [[ ! -f vmci.tar.orig ]]
then
  cp vmci.tar vmci.tar.orig
fi
rm -rf vmci-only
tar xf vmci.tar
pushd vmci-only
patch -p1 < $PATCH_DIR/vmware9.k3.8rc4.patch
popd
tar cf vmci.tar vmci-only
rm -rf vmci-only
popd

