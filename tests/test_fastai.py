import pytest
import json
from fastai.vision import *
from functools import partial
import wandb
from wandb.fastai import WandbCallback

# Tests which rely on row history in memory should set `History.keep_rows = True`
from wandb.history import History
History.keep_rows = True

import sys
import glob


@pytest.fixture
def mnist_data(scope='module'):
    path = untar_data(URLs.MNIST_TINY)
    data = ImageDataBunch.from_folder(path)
    return data


@pytest.fixture
def dummy_model_no_callback(mnist_data):
    learn = cnn_learner(mnist_data, models.squeezenet1_1, metrics=[accuracy])
    return learn


@pytest.fixture
def dummy_model_with_callback(mnist_data):
    learn = cnn_learner(mnist_data,
                        models.squeezenet1_1,
                        metrics=[accuracy],
                        callback_fns=WandbCallback)
    return learn


@pytest.fixture
def dummy_model_with_callback_images(mnist_data):
    learn = cnn_learner(mnist_data,
                        models.squeezenet1_1,
                        metrics=[accuracy],
                        callback_fns=partial(WandbCallback,
                                             input_type='images'))
    return learn


def test_fastai_callback_in_model(wandb_init_run, dummy_model_with_callback):
    dummy_model_with_callback.fit(1)
    wandb.run.summary.load()
    assert wandb.run.history.rows[0]["epoch"] == 0
    assert wandb.run.summary["accuracy"] > 0
    assert wandb.run.summary['graph_0'].to_json()
    assert len(glob.glob(wandb.run.dir + "/bestmodel.pth")) == 1


def test_fastai_callback_in_training(wandb_init_run, dummy_model_no_callback):
    dummy_model_no_callback.fit(
        1, callbacks=WandbCallback(dummy_model_no_callback))
    wandb.run.summary.load()
    assert wandb.run.history.rows[0]["epoch"] == 0
    assert wandb.run.summary["accuracy"] > 0
    assert wandb.run.summary['graph_0'].to_json()
    assert len(glob.glob(wandb.run.dir + "/bestmodel.pth")) == 1


def test_fastai_no_save_model(wandb_init_run, dummy_model_no_callback):
    dummy_model_no_callback.fit(1,
                                callbacks=WandbCallback(
                                    dummy_model_no_callback, save_model=False))
    assert len(glob.glob(wandb.run.dir + "/bestmodel.pth")) == 0


def test_fastai_images(wandb_init_run, dummy_model_with_callback_images):
    dummy_model_with_callback_images.fit(1)
    assert len(
        wandb.run.history.rows[0]["Prediction Samples"]['captions']) == 36
    assert wandb.run.history.rows[0]["Prediction Samples"]['captions']
