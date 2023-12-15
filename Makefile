# Makefile

all:	osu350 gf180

osu350: test/osu350/osu350.yml
	$(shell test/osu350/fetch_spice.sh)
	charlib run test/osu350

gf180: test/gf180/gf180.yml
	$(shell test/gf180/fetch_spice.sh)
	charlib run test/gf180

clean:
	rm -rf __pycache__
	rm -f *~
