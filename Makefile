#!/Makefile

make:
	/bin/rm -rf work/*
	python3 gen_cmd.py
	time python3 libretto.py -b libretto.cmd
#	lc_shell -f run_lc.tcl 
