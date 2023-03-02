# Makefile

all:	setup osu350

setup:
	mkdir -p ./work

gencmd: setup
	python3 gen_cmd.py

osu350:	CharLib.py test/spice_osu350/OSU350.cmd
	$(shell test/spice_osu350/fetch_spice.sh)
	python3 CharLib.py -b test/spice_osu350/OSU350.cmd

gf180mcu: setup CharLib.py test/spice_gf180mcu/gf180mcu.cmd
	python3 CharLib.py -b test/spice_gf180mcu/gf180mcu.cmd

clean:
	rm -rf __pycache__
	rm -f *~

