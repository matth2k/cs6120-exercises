#!/bin/bash
# ./recompile.sh <bril-file> <brili-arg>
blocks=$(bril2json < $1 | deno run brili.ts $2 -p | python3 findHotPath.py)
bril2json < $1 | python3 insertTrace.py -b $blocks | brili $2 -p