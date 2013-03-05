#!/bin/bash

perl -p -i -e 's/name="title_vertical_pad" value="[0-9]+"/name="title_vertical_pad" value="0"/g' /usr/share/themes/Adwaita/metacity-1/*
