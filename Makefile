# Makefile

all:	setup run

setup:
	mkdir -p ./work

run:	CharLib.py CharLib.cmd
	python3 utils/gen_cmd.py
	python3 CharLib.py -b CharLib.cmd

clean:
	rm -rf work
	rm -rf __pycache__
	rm -f *~

