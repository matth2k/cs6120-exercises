BRIL_DIR=/home/matth2k/bril
DOT_GEN=$(BRIL_DIR)/examples/cfg_dot.py

.PHONY: all clean

all: cordic.bril cordic_cfg.png

clean:
	rm -f *.bril *.dot *.png

%.json: %.ts
	echo "{" > $@
	echo " \"functions\": [" >> $@
	ts2bril $< | tail -n +8 >> $@

%.bril: %.json
	bril2txt < $< > $@

%_cfg.dot: %.json
	python3 $(DOT_GEN) < $< | sed 's/\./_/g' > $@

%_cfg.png: %_cfg.dot
	dot $< -Tpng -o $@
