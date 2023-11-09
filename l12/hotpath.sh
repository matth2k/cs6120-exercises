#!/bin/bash
# ./hotpath.sh <bril-file> <brili-args>
bril2json < $1 | deno run brili.ts $2 $3 $4 2> /dev/null | python3 findHotPath.py 
