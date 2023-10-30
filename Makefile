# Makefile

all:	osu350 gf180

osu350: CharLib.py test/osu350/osu350.yml
	$(shell test/osu350/fetch_spice.sh)
	python3 CharLib.py test/osu350

gf180: CharLib.py test/gf180/gf180.yml
	$(shell test/gf180/fetch_spice.sh)
	python3 CharLib.py test/gf180

clean:
	rm -rf __pycache__
	rm -f *~

