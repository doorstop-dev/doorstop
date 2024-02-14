#!/usr/bin/env bash

output=$(make test-cover 2>&1)
result=$(echo "${output}" | grep 'Missing lines')

if [ -n "$result" ]; then
  echo "$output"
  exit 1
fi
