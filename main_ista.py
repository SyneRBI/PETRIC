"""Main file to modify for submissions. It is used by e.g. example.ipynb and petric.py as follows:

>>> from main import Submission, submission_callbacks
>>> from petric import data, metrics
>>> algorithm = Submission(data)
>>> algorithm.run(np.inf, callbacks=metrics + submission_callbacks)
"""
from cil.optimisation.algorithms import GD, ISTA, Algorithm
from cil.optimisation.functions import SGFunction, IndicatorBox
from cil.optimisation.utilities import ConstantStepSize, Sampler, callbacks
from petric import Dataset
from sirf.contrib.partitioner import partitioner

assert issubclass(GD, Algorithm)


class MaxIteration(callbacks.Callback):
    """
    The organisers try to `Submission(data).run(inf)` i.e. for infinite iterations (until timeout).
    This callback forces stopping after `max_iteration` instead.
    """
    def __init__(self, max_iteration: int, verbose: int = 1):
        super().__init__(verbose)
        self.max_iteration = max_iteration

    def __call__(self, algorithm: Algorithm):
        if algorithm.iteration >= self.max_iteration:
            raise StopIteration


class Submission(ISTA):
    # note that `issubclass(GD, Algorithm) == True`
    def __init__(self, data: Dataset, num_subsets: int = 7, step_size: float = 1e-7,
                 update_objective_interval: int = 10):
        """
        Initialisation function, setting up data & (hyper)parameters.
        NB: in practice, `num_subsets` should likely be determined from the data.
        WARNING: we also currently ignore the non-negativity constraint here.
        This is just an example. Try to modify and improve it!
        """
        data_sub, acq_models, obj_funs = partitioner.data_partition(data.acquired_data, data.additive_term,
                                                                    data.mult_factors, num_subsets, mode='staggered',
                                                                    initial_image=data.OSEM_image)
        for f in obj_funs: # add prior to every objective function
            f.set_prior(data.prior)

        sampler = Sampler.random_without_replacement(len(obj_funs))
        F = -SGFunction(obj_funs, sampler=sampler)   # negative to turn minimiser into maximiser
        step_size_rule = ConstantStepSize(step_size) # ISTA default step_size is 0.99*2.0/F.L

        g = IndicatorBox(lower=1e-5, accelerated=False)

        super().__init__(initial=data.OSEM_image.get_uniform_copy(1.),
                         f=F, g=g, step_size=step_size_rule,
                         update_objective_interval=update_objective_interval)


submission_callbacks = [MaxIteration(1000)]
