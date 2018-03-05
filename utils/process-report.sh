#!/bin/bash -e

REPORT_FILE=$1
DEST_DIR=cam-tmp-$(date +%s)

if [ -z "${REPORT_FILE}" ]; then
	echo "Usage: $0 <report-file>"
	exit 1
fi

for LABEL in $(grep -v '^#' ${REPORT_FILE} | cut -d: -f1 | sort | uniq); do
	mkdir -vp ${DEST_DIR}/${LABEL}
done

grep -v '^#' ${REPORT_FILE} | grep -v unknown: | awk -F: -v DEST_DIR=${DEST_DIR} '/^[^#]/{ LABEL=$1; SRC=$2; DST=SRC; gsub(".*/events/", "", DST); gsub("/", "-", DST); print("cp -v " SRC " " DEST_DIR "/" LABEL "/" DST);}' | bash -
echo "Temporary files are in ${DEST_DIR}/"
