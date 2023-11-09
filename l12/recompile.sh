#!/bin/bash -e
# ./recompile.sh <bril-file> <brili-arg>
set -o pipefail
blocks=$(bril2json < $1 | deno run brili.ts $2 $3 $4 -p | python3 findHotPath.py)
bril2json < $1 | python3 insertTrace.py -v -b $blocks | brili $2 $3 $4 -p