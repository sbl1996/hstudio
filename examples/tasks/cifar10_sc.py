from toolz import curry

import tensorflow as tf
from tensorflow.keras.metrics import CategoricalAccuracy, Mean, CategoricalCrossentropy

from hanser.distribute import setup_runtime, distribute_datasets
from hanser.datasets.cifar import make_cifar10_dataset
from hanser.transform import random_crop, normalize, to_tensor

from hanser.train.optimizers import SGD
from hanser.models.cifar.resnet import resnet110
from hanser.train.cls import SuperLearner
from hanser.train.lr_schedule import OneCycleLR
from hanser.losses import CrossEntropy


@curry
def transform(image, label, training):
    if training:
        image = random_crop(image, (32, 32), (4, 4))
        image = tf.image.random_flip_left_right(image)

    image, label = to_tensor(image, label)
    image = normalize(image, [0.491, 0.482, 0.447], [0.247, 0.243, 0.262])

    label = tf.one_hot(label, 10)

    return image, label


batch_size = 128
eval_batch_size = 2048

ds_train, ds_test, steps_per_epoch, test_steps = make_cifar10_dataset(
    batch_size, eval_batch_size, transform)

setup_runtime(fp16=True)
ds_train, ds_test = distribute_datasets(ds_train, ds_test)

model = resnet110(num_classes=10)
model.build((None, 32, 32, 3))
model.summary()

criterion = CrossEntropy()

max_lr = 1.0
epochs = 20
lr_schedule = OneCycleLR(max_lr, steps_per_epoch, epochs=epochs, pct_start=0.45, div_factor=10)
optimizer = SGD(lr_schedule, momentum=0.9, weight_decay=5e-4, nesterov=True)
train_metrics = {
    'loss': Mean(),
    'acc': CategoricalAccuracy(),
}
eval_metrics = {
    'loss': CategoricalCrossentropy(from_logits=True),
    'acc': CategoricalAccuracy(),
}

learner = SuperLearner(
    model, criterion, optimizer,
    train_metrics=train_metrics, eval_metrics=eval_metrics,
    work_dir=f"./models")

learner.fit(ds_train, epochs, ds_test, val_freq=1,
            steps_per_epoch=steps_per_epoch, val_steps=test_steps,
            reuse_train_iterator=True)

import tensorflow_datasets as tfds
tfds.load()