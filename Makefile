# Makefile

all:	osu350_lib

setup:
	mkdir -p ./work

gencmd: setup
	python3 gen_cmd.py

osu350:	CharLib.py test/osu350/OSU350.cmd setup
	$(shell test/osu350/fetch_spice.sh)
	python3 CharLib.py -b test/osu350/OSU350.cmd

osu350_lib: CharLib.py test/osu350/osu350.yml
	$(shell test/osu350/fetch_spice.sh)
	python3 CharLib.py -l test/osu350

gf180: CharLib.py
	$(shell test/gf180/fetch_spice.sh)

clean:
	rm -rf __pycache__
	rm -f *~

