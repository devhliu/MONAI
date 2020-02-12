# Copyright 2020 MONAI Consortium
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest
import warnings

import torch

from monai.application.engine import create_multigpu_supervised_trainer


def fake_loss(y_pred, y):
    return (y_pred[0] + y).sum()


def fake_data_stream():
    while True:
        yield torch.rand((10, 1, 64, 64)), torch.rand((10, 1, 64, 64))

def expect_failure_if_no_gpu(test):
    if not torch.cuda.is_available():
        return unittest.expectedFailure(test)
    else:
        return test


class TestParallelExecution(unittest.TestCase):
    """
    Tests single GPU, multi GPU, and CPU execution with the Ignite supervised trainer.
    """

    @expect_failure_if_no_gpu
    def test_single_gpu(self):
        net = torch.nn.Conv2d(1, 1, 3, padding=1)
        opt = torch.optim.Adam(net.parameters(), 1e-3)
        trainer = create_multigpu_supervised_trainer(net, opt, fake_loss, [torch.device("cuda:0")])
        trainer.run(fake_data_stream(), 2, 2)

    @expect_failure_if_no_gpu
    def test_multi_gpu(self):
        net = torch.nn.Conv2d(1, 1, 3, padding=1)
        opt = torch.optim.Adam(net.parameters(), 1e-3)

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")  # ignore warnings about imbalanced GPU memory

            trainer = create_multigpu_supervised_trainer(net, opt, fake_loss, None)

        trainer.run(fake_data_stream(), 2, 2)

    def test_cpu(self):
        net = torch.nn.Conv2d(1, 1, 3, padding=1)
        opt = torch.optim.Adam(net.parameters(), 1e-3)
        trainer = create_multigpu_supervised_trainer(net, opt, fake_loss, [])
        trainer.run(fake_data_stream(), 2, 2)
