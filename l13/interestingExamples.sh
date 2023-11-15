#!/bin/bash
set +x
python3 smt.py --help
python3 smt.py "8*(x[7:0] + (x[15:8] << 8))" -N 16
python3 smt.py "8*(x[7:0] + (x[15:8] << 8))" -N 24
python3 smt.py "20x^2 - 20x" -N 16