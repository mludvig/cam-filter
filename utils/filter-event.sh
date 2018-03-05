#!/bin/bash -e

MODEL=camera1.model
BASE_PATH=/var/lib/zoneminder
#ZM_URL=https://localhost/zm
ZM_URL=https://hlinik.fritz.box/zm

REPORT_PATH=/tmp/report-$(date +%s)
REPORT_EVENT=${REPORT_PATH}/report-event-%d.log
REPORT_JSON=${REPORT_PATH}/report.json
REPORT_LOG=${REPORT_PATH}/report.log

EVENT_ID=$1

if [ -z "${EVENT_ID}" ]; then
	echo "Usage: $0 <event-id>"
	exit 1
fi

mkdir -p ${REPORT_PATH}
test -f ${REPORT_JSON} || echo '[]' > ${REPORT_JSON}
while (true) do
	echo "Processing Event-${EVENT_ID}"

	EVENT_RAW=$(curl -s -k ${ZM_URL}/api/events/${EVENT_ID}.json | jq 'del(.event.Frames)')
	if [ $(jq -r .success <<< ${EVENT_RAW}) == "false" ]; then
		set +x
		jq -r .data.message <<< ${EVENT_RAW} >&2
		exit 1
	fi

	EVENT=$(jq '.event | {"EventId": .Event.Id, "MonitorId": .Monitor.Id, "Path": .Event.BasePath, "StartTime": .Event.StartTime, "Length": .Event.Length, "Frames": .Event.Frames, "AlarmFrames": .Event.AlarmFrames, "TotScore": .Event.TotScore, "MaxScore": .Event.MaxScore, "AvgScore": .Event.AvgScore, "Width": .Event.Width, "Height": .Event.Height, "Next": .Event.NextOfMonitor }' <<< ${EVENT_RAW})

	EVENT_PATH=$(jq -r .Path <<< ${EVENT})
	START_TIME=$(jq -r .StartTime <<< ${EVENT})
	LENGTH=$(jq -r .Length <<< ${EVENT})
	FRAMES=$(jq -r .Frames <<< ${EVENT})

	echo -e "\e[1mEvent-${EVENT_ID} [${START_TIME} / ${LENGTH}s]\e[0m"
	echo "Path: ${BASE_PATH}/${EVENT_PATH} (${FRAMES} frames)"
	echo

	REPORT_FILE=$(printf ${REPORT_EVENT} ${EVENT_ID})
	python -W ignore ./analyse-event.py --model ${MODEL} --dataset ${BASE_PATH}/${EVENT_PATH} --report ${REPORT_FILE}
	RESULT=$(tail -n1 ${REPORT_FILE})

	echo "Event-${EVENT_ID} ${BASE_PATH}/${EVENT_PATH} ${START_TIME} ${LENGTH}s ${FRAMES} ${RESULT}" | tee -a ${REPORT_LOG}
	RESULT_LABEL=$(cut -d\  -f1 <<< ${RESULT})
	RESULT_PMAX=$(cut -d= -f2 <<< ${RESULT} | cut -d% -f1)
	EVENT=$(jq --arg _label "${RESULT_LABEL}" --arg _pmax "${RESULT_PMAX}" '. + { "Label": $_label, "Pmax": $_pmax }' <<< ${EVENT})
	jq --argjson append "[${EVENT}]" '. += $append' ${REPORT_JSON} > ${REPORT_JSON}.$$
	mv -fv ${REPORT_JSON}.$$ ${REPORT_JSON}

	if [ "${RESULT:0:6}" == "PEOPLE" ]; then
		echo -e "\e[32;1mRetaining Event-${EVENT_ID} [${RESULT}]\e[0m"
	else
		echo -e "\e[31;1mDeleting Event-${EVENT_ID} [${RESULT}]\e[0m"
	fi
	echo ==================
	echo

	EVENT_ID=$(jq -r .Next <<< ${EVENT})
	test "${EVENT_ID}" == "null" && break

	#echo -n "Next event: ${EVENT_ID}. Proceed? [Y/n] "
	#read ANS
	#test "${ANS}" == "n" -o "${ANS}" == "N" && break
done

echo
echo "### Reports are in ${REPORT_PATH} ###"
echo
