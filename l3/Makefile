BRIL_DIR=/home/matth2k/bril
BENCH_DIRS=$(BRIL_DIR)/benchmarks
BENCH_RESULTS=core.csv float.csv mem.csv mixed.csv


.PHONY: all tests clean

all: tests

tests: $(BENCH_RESULTS)
	cat $^ > all.csv

%.csv:
	echo "benchmarks = '$(BENCH_DIRS)/$*/*.bril'" > $*.toml
	cat benchmarks.toml >> $*.toml
	brench $*.toml > $@
	rm $*.toml

clean:
	rm -f *.csv
