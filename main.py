"""Main file to modify for submissions. It is used by e.g. example.ipynb and petric.py as follows:

>>> from main import Submission, submission_callbacks
>>> from petric import data, metrics
>>> algorithm = Submission(data)
>>> algorithm.run(np.inf, callbacks=metrics + submission_callbacks)
"""
from cil.optimisation.algorithms import Algorithm
from cil.optimisation.utilities import callbacks
from petric import Dataset
from sirf.contrib.BSREM.BSREM import BSREM1

assert issubclass(BSREM1, Algorithm)


class MaxIteration(callbacks.Callback):
    def __init__(self, max_iteration: int, verbose: int = 1):
        super().__init__(verbose)
        self.max_iteration = max_iteration

    def __call__(self, algorithm: Algorithm):
        if algorithm.iteration >= self.max_iteration:
            raise StopIteration


class Submission(BSREM1):
    def __init__(self, data: Dataset, num_subsets: int = 7, update_objective_interval: int = 10):
        super().__init__(data.data, data.obj_funs, initial=data.OSEM_image, initial_step_size=.3, relaxation_eta=.01,
                         update_objective_interval=update_objective_interval)


submission_callbacks = [MaxIteration(660)]
