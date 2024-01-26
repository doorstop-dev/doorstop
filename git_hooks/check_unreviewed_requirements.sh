#!/usr/bin/env bash

output="$(doorstop -W 2>&1 | grep 'unreviewed changes')"

if [ -n "$output" ]; then
  echo "$output"
  exit 1
fi
