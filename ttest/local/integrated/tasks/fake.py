import time

import numpy as np

from toolz import curry

from hhutil.io import time_now

epochs = 20

train_time = 2
test_time = 0.3


def interp(ratio, min_val, max_val):
    return ratio * (max_val - min_val) + min_val

def gen_metric_cos(ratio, max_val, min_val, noise, nl_map):
    ratio = nl_map(ratio) + noise
    ratio = np.clip(ratio, 0, 1)
    val = interp(ratio, min_val, max_val)
    return val


@curry
def poly_map(ratio, min_val=0.0):
    return interp(ratio, min_val, 1.0) ** 4


def linear_map(ratio):
    return ratio

print("%s Start training" % time_now())
for i in range(epochs):
    ratio = 1 - (i + 1) / epochs
    stddev = interp(ratio, 0, 0.01)
    train_noise = np.random.normal(0, stddev)
    train_loss = gen_metric_cos(ratio, 2.5, 0.0, train_noise, poly_map(min_val=0.2))
    train_acc = gen_metric_cos(1 - ratio, 1.0, 0.0, train_noise, linear_map)

    test_noise = np.random.normal(0, 0.01)
    test_loss = gen_metric_cos(ratio, 2.5, 0.6, test_noise, poly_map(min_val=0.4))
    test_acc = gen_metric_cos(1 - ratio, 0.8, 0.0, test_noise, linear_map)
    print("Epoch %d/%d" % (i + 1, epochs))
    time.sleep(train_time)
    print("%s train - loss: %.4f, acc: %.4f" % (time_now(), train_loss, train_acc))
    time.sleep(test_time)
    print("%s valid - loss: %.4f, acc: %.4f" % (time_now(), test_loss, test_acc))