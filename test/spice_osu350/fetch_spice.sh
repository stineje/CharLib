#!/bin/bash

TARGET_DIR='spice_temp'
SOURCE='https://vlsiarch.ecen.okstate.edu/flows/MOSIS_SCMOS/latest/cadence/lib/ami035/signalstorm/osu035_stdcells.sp'
TEMP_SP_FILENAME='osu035_stdcells.sp.temp'

mkdir -p $TARGET_DIR

# Download source
curl -s $SOURCE > $TEMP_SP_FILENAME

# Split into separate files
awk -v RS= '{print > ("temp_cell_" NR ".sp.temp")}' $TEMP_SP_FILENAME
rm $TEMP_SP_FILENAME

# Correct cell filenames
for TEMP_CELL_FILENAME in `ls *.sp.temp`
do
    decl=$(head -n1 $TEMP_CELL_FILENAME)
    decl_words=($decl)
    cell_name=${decl_words[1]}
    mv $TEMP_CELL_FILENAME $TARGET_DIR/$cell_name.sp
done
