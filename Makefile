# Makefile

all:	setup osu350_lib

setup:
	mkdir -p ./work

gencmd: setup
	python3 gen_cmd.py

osu350:	CharLib.py test/spice_osu350/OSU350.cmd
	$(shell test/spice_osu350/fetch_spice.sh)
	python3 CharLib.py -b test/spice_osu350/OSU350.cmd

osu350_lib: CharLib.py test/spice_osu350/osu350.yml
	$(shell test/spice_osu350/fetch_spice.sh)
	python3 CharLib.py -l test/spice_osu350

gf180mcu: setup CharLib.py test/spice_gf180mcu/gf180mcu.cmd
	python3 CharLib.py -b test/spice_gf180mcu/gf180mcu.cmd

clean:
	rm -rf __pycache__
	rm -f *~

