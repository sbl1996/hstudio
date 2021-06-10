PID=$(ps aux | grep "[u]vicorn hstudio.service.host:app" | awk '{print $2}')
if [ -z "$PID" ]
then
  echo "No runing host."
else
  kill -9 "$PID"
  echo "Kill running host $PID."
fi