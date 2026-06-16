#! /usr/bin/env bash

export OSU035_COMMIT="b36db529c2dff117e1fbead561bf792ec866e1cb"
mkdir -p osu350/spice
mkdir -p osu350/models
curl -fsSL --retry 3 https://raw.githubusercontent.com/stineje/MOSIS_SCMOS/$OSU035_COMMIT/latest/cadence/lib/ami035/signalstorm/osu035_stdcells.sp > osu350/spice/osu035_stdcells.sp
curl -fsSL --retry 3 https://raw.githubusercontent.com/stineje/MOSIS_SCMOS/$OSU035_COMMIT/latest/cadence/lib/ami035/lib/ami035.m > osu350/models/ami035.m
curl -fsSL --retry 3 https://raw.githubusercontent.com/stineje/CharLib/refs/heads/main/test/pdks/osu350/fix_hspice_models.patch > osu350/fix_hspice_models.patch
patch -s osu350/models/ami035.m osu350/fix_hspice_models.patch
