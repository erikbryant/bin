#!/bin/bash

KVER=`uname -r`
cp /usr/src/kernels/$KVER/include/generated/uapi/linux/version.h /lib/modules/$KVER/build/include/linux/
