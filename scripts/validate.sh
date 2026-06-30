#!/bin/sh
set -eu

python -m compileall -q .
find static/js -name '*.js' -print0 | xargs -0 -n1 node --check
python -m pytest
