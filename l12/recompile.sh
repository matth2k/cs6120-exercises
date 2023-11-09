#!/bin/bash -e
# ./recompile.sh <bril-file> <brili-arg>
set -o pipefail
echo "Before:"
blocks=$(bril2json < $1 | deno run brili.ts $2 $3 $4 -p | python3 findHotPath.py -v 2> tmp.txt)
echo "After:"
bril2json < $1 | python3 insertTrace.py -v -b $blocks 2>> tmp.txt | brili $2 $3 $4 -p
echo "Transform Report:"
cat tmp.txt