# Makefile

all:	setup run

setup:
	mkdir -p ./work

gencmd: setup
	python3 gen_cmd.py

run:	CharLib.py test/spice_osu350/OSU350.cmd
	python3 CharLib.py -b test/spice_osu350/OSU350.cmd

clean:
	rm -rf work
	rm -rf __pycache__
	rm -f *~

