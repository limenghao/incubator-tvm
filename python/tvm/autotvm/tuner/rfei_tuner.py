# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
"""Tuner that uses RandomForestRegressor+ExpectedImprovement as cost model"""

from .model_based_tuner import ModelOptimizer, ModelBasedTuner
from .sa_model_optimizer import SimulatedAnnealingOptimizer
from .rf_cost_model import RFEICostModel


class RFEITuner(ModelBasedTuner):
    """Tuner that uses RandomForestRegressor+ExpectedImprovement as cost model

    Parameters
    ----------
    task: Task
        The tuning task
    plan_size: int
        The size of a plan. After `plan_size` trials, the tuner will refit a new cost model
        and do planing for the next `plan_size` trials.
    feature_type: str, optional
        If is 'itervar', use features extracted from IterVar (loop variable).
        If is 'knob', use flatten ConfigEntity directly.
        If is 'curve', use sampled curve feature (relation feature).

        Note on choosing feature type:
        For single task tuning, 'itervar' and 'knob' are good.
        'itervar' is more accurate but 'knob' is much faster.
        There are some constraints on 'itervar', if you meet
        problems with feature extraction when using 'itervar',
        you can switch to 'knob'.

        For cross-shape tuning (e.g. many convolutions with different shapes),
        'itervar' and 'curve' has better transferability,
        'knob' is faster.

        For cross-device or cross-operator tuning, you can use 'curve' only.
    num_threads: int, optional
        The number of threads.
    optimizer: str or ModelOptimizer, optional
        If is 'sa', use a default simulated annealing optimizer.
        Otherwise it should be a ModelOptimizer object.
    diversity_filter_ratio: int or float, optional
        If is not None, the tuner will first select
        top-(plan_size * diversity_filter_ratio) candidates according to the cost model
        and then pick batch_size of them according to the diversity metric.
    log_interval: int, optional
        The verbose level.
        If is 0, output nothing.
        Otherwise, output debug information every `verbose` iterations.
    uncertainty_aware: bool, optional
        If it is false, disable the dynamic uncertainty-aware searching process.
    """

    def __init__(
        self,
        task,
        plan_size=32,
        feature_type="itervar",
        num_threads=None,
        optimizer="sa",
        diversity_filter_ratio=None,
        log_interval=50,
        uncertainty_aware=True,
    ):

        cost_model = RFEICostModel(
            task, feature_type=feature_type, num_threads=num_threads, log_interval=log_interval // 2
        )
        if optimizer == "sa":
            optimizer = SimulatedAnnealingOptimizer(
                task, log_interval=log_interval, parallel_size=plan_size * 2
            )
        else:
            assert isinstance(optimizer, ModelOptimizer), (
                "Optimizer must be " "a supported name string" "or a ModelOptimizer object."
            )
        super(RFEITuner, self).__init__(
            task, cost_model, optimizer, plan_size, diversity_filter_ratio, uncertainty_aware
        )

    def tune(self, *args, **kwargs):  # pylint: disable=arguments-differ
        super(RFEITuner, self).tune(*args, **kwargs)

        # manually close pool to avoid multiprocessing issues
        self.cost_model._close_pool()
