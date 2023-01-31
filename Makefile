# Makefile

all:	setup run

setup:
	mkdir -p ./work

gencmd: setup
	python3 gen_cmd.py

run:	CharLib.py CharLib.cmd
	python3 CharLib.py -b CharLib.cmd

clean:
	rm -rf work
	rm -rf __pycache__
	rm -f *~

