#!/bin/bash

set -e

ARGS="$ACTION -o $ORG -r"
if [ -n "$TARGET" ]; then
	ARGS="$ARGS -t $TARGET"
fi
if [ -n "$WORKFLOW" ]; then
	ARGS="$ARGS -w $WORKFLOW"
fi

python3.9 launch.py $ARGS
