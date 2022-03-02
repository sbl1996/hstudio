from hhutil.io import fmt_path, eglob, read_text

from hstudio.utils import encode_script, decode_script

for f in eglob("/Users/hrvvi/Code/Library/experiments/CIFAR100-TensorFlow/code", "*.py"):
    print(f)
    s = read_text(f)
    s1 = encode_script(s)
    s2 = decode_script(s1)
    assert s2 == s