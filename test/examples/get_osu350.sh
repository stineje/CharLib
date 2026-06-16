#! /usr/bin/env bash

mkdir -p osu350/spice
mkdir -p osu350/models
curl -s https://raw.githubusercontent.com/stineje/MOSIS_SCMOS/refs/heads/main/latest/cadence/lib/ami035/signalstorm/osu035_stdcells.sp > osu350/spice/osu035_stdcells.sp
curl -s https://raw.githubusercontent.com/stineje/MOSIS_SCMOS/refs/heads/main/latest/cadence/lib/ami035/lib/ami035.m > osu350/models/ami035.m
curl -s https://raw.githubusercontent.com/stineje/CharLib/refs/heads/main/test/pdks/osu350/fix_hspice_models.patch > osu350/fix_hspice_models.patch
patch -s osu350/models/ami035.m osu350/fix_hspice_models.patch
