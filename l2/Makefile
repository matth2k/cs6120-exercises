BRIL_DIR=/home/matth2k/bril
DOT_GEN=$(BRIL_DIR)/examples/cfg_dot.py

.PHONY: all clean

all: cordic.bril cordic_cfg.png

clean:
	rm -f *.bril *.dot *.png

%.bril: %.ts
	echo "{" > $@
	echo " \"functions\": [" >> $@
	ts2bril $< | tail -n +8 >> $@

%_cfg.dot: %.bril
	python3 $(DOT_GEN) < $< | sed 's/\./_/g' > $@

%_cfg.png: %_cfg.dot
	dot $< -Tpng -o $@
