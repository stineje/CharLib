#!/bin/bash

TARGET_DIR=${PWD}'/gf180_spice_temp'

# Sources for fetching cells
CELL_GIT_SOURCE='https://github.com/stineje/globalfoundries-pdk-libs-gf180mcu_osu_sc'
CELL_COMMIT='df1d8ec95b'
CELL_DIR='globalfoundries-pdk-libs-gf180mcu_osu_sc/gf180mcu_osu_sc_gp12t3v3/cells'

# Source for fetching models
MODEL_SOURCE='https://github.com/google/globalfoundries-pdk-libs-gf180mcu_fd_pr/blob/main/models/ngspice/sm141064.ngspice'
MODEL_FILENAME='sm141064.spice'

mkdir -p $TARGET_DIR
pushd $TARGET_DIR > /dev/null

# Fetch cells from a tested commit hash
git clone $CELL_GIT_SOURCE
cd globalfoundries-pdk-libs-gf180mcu_osu_sc/
git checkout $CELL_COMMIT
cd ..
for CELL_FILE in `find "$CELL_DIR" -type f -name "*.spice"`
do
    cp $CELL_FILE $TARGET_DIR/.
done
rm -rf globalfoundries-pdk-libs-gf180mcu_osu_sc/

# Fetch transistor models
curl -s $MODEL_SOURCE > $MODEL_FILENAME

popd > /dev/null