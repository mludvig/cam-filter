#!/bin/sh

# Parse report logs and copy misclassified files to cam-tmp/{people,nothing}
# Usage: $0 reports/Event-*.log

mkdir -p cam-tmp/people cam-tmp/nothing
awk -F: '($1 == "nothing" && $2>50) || ($1 == "people" && $2<50) { dst=$3; sub(".*/events/", "", dst); gsub("/", "-", dst); print("cp -v " $3 " cam-tmp/" $1 "/" dst);}' $* | sh
