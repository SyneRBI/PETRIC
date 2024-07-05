"""Main file to modify for submissions. It is used by e.g. example.ipynb and petric.py as follows:

>>> from main import Submission, submission_callbacks
>>> from petric import data, metrics
>>> algorithm = Submission(data)
>>> algorithm.run(np.inf, callbacks=metrics + submission_callbacks)
"""
from cil.optimisation.algorithms import ISTA, Algorithm
from cil.optimisation.functions import IndicatorBox, SGFunction
from cil.optimisation.utilities import ConstantStepSize, Sampler, callbacks, Preconditioner, StepSizeRule
from petric import Dataset
from sirf.contrib.partitioner import partitioner
import numpy as np

assert issubclass(ISTA, Algorithm)


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

class MyPreconditioner(Preconditioner):
    # See:
    # Tsai, Y.-J., Bousse, A., Ehrhardt, M.J., Stearns, C.W., Ahn, S., Hutton, B., Arridge, S., Thielemans, K., 2017. 
    # Fast Quasi-Newton Algorithms for Penalized Reconstruction in Emission Tomography and Further Improvements via Preconditioning. 
    # IEEE Transactions on Medical Imaging 1. https://doi.org/10.1109/tmi.2017.2786865
    def __init__(self, kappa):
        self.kappasq = kappa * kappa + 1e-5
        
    def apply(self, algorithm, gradient, out):
        out = gradient.divide(self.kappasq, out=out)
        return out
    
class OSEMStepSize(StepSizeRule):
    '''Step size rule for OSEM algorithm.
    
    ::math::
        x^+ = x + t \nabla \log L(y|x)
        
    with :math:`t = x / s` where :math:`s` is the adjoint of the range geometry of the acquisition model.
    '''
    def __init__(self, acq_models):
        self.reciproc_s = []

        for i,el in enumerate(acq_models):
            ones = el.range_geometry().allocate(1.)
            s = el.adjoint(ones)
            arr = s.as_array()
            np.reciprocal(arr, out=arr)
            np.nan_to_num(arr, copy=False, nan=0, posinf=0, neginf=0)
            s.fill(arr)
            self.reciproc_s.append(s)
    
    def get_step_size(self, algorithm):
        """
        Returns
        --------
        the calculated step size:float 
        """
        func_num = algorithm.f.function.function_num
        t = algorithm.solution * self.reciproc_s[func_num]
        return t

class Submission(ISTA):
    # note that `issubclass(ISTA, Algorithm) == True`
    def __init__(self, data: Dataset, num_subsets: int = 7, step_size: float = 1e-6,
                 update_objective_interval: int = 10):
        """
        Initialisation function, setting up data & (hyper)parameters.
        NB: in practice, `num_subsets` should likely be determined from the data.
        This is just an example. Try to modify and improve it!
        """
        data_sub, acq_models, obj_funs = partitioner.data_partition(data.acquired_data, data.additive_term,
                                                                    data.mult_factors, num_subsets, mode='staggered',
                                                                    initial_image=data.OSEM_image)
        for f in obj_funs: # add prior to every objective function
            f.set_prior(data.prior)

        sampler = Sampler.random_without_replacement(len(obj_funs))
        F = -SGFunction(obj_funs, sampler=sampler)      # negative to turn minimiser into maximiser
        # Uncomment the following for the constant step size rule
        # step_size_rule = ConstantStepSize(0.1)    # ISTA default step_size is 0.99*2.0/F.L
        # Uncomment the following for the OSEM step size rule
        step_size_rule = OSEMStepSize(acq_models)
        
        g = IndicatorBox(lower=1e-6, accelerated=False) # "non-negativity" constraint

        my_preconditioner = MyPreconditioner(data.kappa)
        super().__init__(initial=data.OSEM_image,
                         f=F, g=g, step_size=step_size_rule,
                         preconditioner=my_preconditioner,
                         update_objective_interval=update_objective_interval)


submission_callbacks = [MaxIteration(1000)]
