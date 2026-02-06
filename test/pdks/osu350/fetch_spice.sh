#!/bin/bash

TARGET_DIR='osu350_spice_temp'
SOURCE='https://raw.githubusercontent.com/stineje/MOSIS_SCMOS/main/latest/cadence/lib/ami035/signalstorm/osu035_stdcells.sp'
TEMP_SP_FILENAME='osu035_stdcells.sp.temp'

mkdir -p $TARGET_DIR
pushd $TARGET_DIR > /dev/null

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
    mv $TEMP_CELL_FILENAME $cell_name.sp
done

popd > /dev/null
