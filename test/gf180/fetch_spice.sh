#!/bin/bash

TARGET_DIR=${PWD}'/gf180_temp'

# Sources for fetching cells
CELL_GIT_SRC='https://github.com/stineje/globalfoundries-pdk-libs-gf180mcu_osu_sc'
CELL_COMMIT='df1d8ec95b'
CELL_DIR='globalfoundries-pdk-libs-gf180mcu_osu_sc/gf180mcu_osu_sc_gp12t3v3/cells'

# Source for fetching models
MODEL_SRC='https://raw.githubusercontent.com/google/globalfoundries-pdk-libs-gf180mcu_fd_pr/main/models/ngspice'
MODEL1_FILENAME='sm141064.ngspice'
MODEL2_FILENAME='design.ngspice'

rm -rf $TARGET_DIR
mkdir $TARGET_DIR
pushd $TARGET_DIR > /dev/null
mkdir cells
mkdir models

# Fetch cells from a tested commit hash
git clone $CELL_GIT_SRC
cd globalfoundries-pdk-libs-gf180mcu_osu_sc/
git checkout $CELL_COMMIT
cd ..
for CELL_FILE in `find "$CELL_DIR" -type f -name "*.spice"`
do
    sed -i 's/fet_03p3/mos_3p3/' $CELL_FILE
    cp $CELL_FILE $TARGET_DIR/cells/.
done
rm -rf globalfoundries-pdk-libs-gf180mcu_osu_sc/

# Fetch transistor models
curl -s $MODEL_SRC/$MODEL1_FILENAME > models/$MODEL1_FILENAME
curl -s $MODEL_SRC/$MODEL2_FILENAME > models/$MODEL2_FILENAME

popd > /dev/null
