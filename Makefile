#!/Makefile

make:
	/bin/rm -rf work/*
	python3 gen_cmd.py
	time python3 CharLib.py -b CharLib.cmd
#	lc_shell -f run_lc.tcl 
