PID=$(ps aux | grep "[u]vicorn hstudio.service.host:app" | awk '{print $2}')
if [ ! -z "$PID" ]
then
  echo "Host ($PID) is runing."
  exit 1
fi

CUR_DATE=$(date +'%Y-%m-%d_%H:%M:%S')
mkdir -p logs
LOG_FILE="logs/$CUR_DATE.log"

if [ ! -z "$ROOT_PATH" ]
then
  nohup uvicorn hstudio.service.host:app --root-path "$ROOT_PATH" > "$LOG_FILE" 2>&1 &
else
  nohup uvicorn hstudio.service.host:app > "$LOG_FILE" 2>&1 &
fi


echo "Host started, logging to $LOG_FILE"
rm -f "logs/run.log"
ln -s "$CUR_DATE.log" "logs/run.log"