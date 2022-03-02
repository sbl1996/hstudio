import time
import subprocess
from hhutil.io import fmt_path

log_file = fmt_path("/Users/hrvvi/Downloads/1.log")
script_file = fmt_path("/Users/hrvvi/Code/Library/hstudio/tests/test_subprocess/fake.py")

sync_file = fmt_path("/Users/hrvvi/Downloads/2.log")

p = subprocess.Popen(f"python -u {script_file} > {log_file} 2>&1", shell=True)
time.sleep(1)
pos = 0
sync_file_f = sync_file.open("w+", buffering=1)
while p.poll() is None:
    new_pos = log_file.stat().st_size
    sync_file_f.write(log_file.read_text()[pos:new_pos])
    # print(log_file.read_text()[pos:new_pos], end='')
    pos = new_pos
    time.sleep(1)
print("Finished with %d." % p.returncode)