"""Main file to modify for submissions.

Once renamed or symlinked as `main.py`, it will be used by `petric.py` as follows:

>>> from main import Submission, submission_callbacks
>>> from petric import data, metrics
>>> algorithm = Submission(data)
>>> algorithm.run(np.inf, callbacks=metrics + submission_callbacks)
"""
import sirf.STIR as STIR
from cil.optimisation.algorithms import Algorithm
from cil.optimisation.utilities import callbacks
from petric import Dataset
from sirf.contrib.partitioner.partitioner import partition_indices


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


class Submission(Algorithm):
    """
    OSEM algorithm example.
    NB: In OSEM, the multiplicative term cancels in the back-projection of the quotient of measured & estimated data
    (so this is used here for efficiency). Note that a similar optimisation can be used for all algorithms using the Poisson log-likelihood.
    NB: OSEM does not use `data.prior` and thus does not converge to the MAP reference used in PETRIC.
    NB: this example does not use the `sirf.STIR` Poisson objective function.
    NB: see https://github.com/SyneRBI/SIRF-Contribs/tree/master/src/Python/sirf/contrib/BSREM
    """
    def __init__(self, data: Dataset, num_subsets: int = 7, update_objective_interval: int = 10, **kwargs):
        """
        Initialisation function, setting up data & (hyper)parameters.
        NB: in practice, `num_subsets` should likely be determined from the data.
        This is just an example. Try to modify and improve it!
        """
        self.acquisition_models = []
        self.prompts = []
        self.sensitivities = []
        self.subset = 0
        self.x = data.OSEM_image.clone()

        # find views in each subset
        # (note that SIRF can currently only do subsets over views)
        views = data.mult_factors.dimensions()[2]
        partitions_idxs = partition_indices(num_subsets, list(range(views)), stagger=True)

        # for each subset: find data, create acq_model, and create subset_sensitivity (backproj of 1)
        for i in range(num_subsets):
            prompts_subset = data.acquired_data.get_subset(partitions_idxs[i])
            additive_term_subset = data.additive_term.get_subset(partitions_idxs[i])
            multiplicative_factors_subset = data.mult_factors.get_subset(partitions_idxs[i])

            acquisition_model_subset = STIR.AcquisitionModelUsingParallelproj()
            acquisition_model_subset.set_additive_term(additive_term_subset)
            acquisition_model_subset.set_up(prompts_subset, self.x)

            subset_sensitivity = acquisition_model_subset.backward(multiplicative_factors_subset)
            # add a small number to avoid NaN in division
            subset_sensitivity += subset_sensitivity.max() * 1e-6

            self.acquisition_models.append(acquisition_model_subset)
            self.prompts.append(prompts_subset)
            self.sensitivities.append(subset_sensitivity)

        super().__init__(update_objective_interval=update_objective_interval, **kwargs)
        self.configured = True # required by Algorithm

    def update(self):
        # compute forward projection for the denomintor
        # add a small number to avoid NaN in division, as OSEM lead to 0/0 or worse.
        # (Theoretically, MLEM cannot, but it might nevertheless due to numerical issues)
        denom = self.acquisition_models[self.subset].forward(self.x) + .0001
        # divide measured data by estimate (ignoring mult_factors!)
        quotient = self.prompts[self.subset] / denom

        # update image with quotient of the backprojection (without mult_factors!) and the sensitivity
        self.x *= self.acquisition_models[self.subset].backward(quotient) / self.sensitivities[self.subset]
        self.subset = (self.subset + 1) % len(self.prompts)

    def update_objective(self):
        # should do some stuff here to have a correct TensorBoard display, but the
        # objective function value is not part of the challenge, we will take an ugly short-cut.
        # If you need it, you can implement it as a sum over subsets of something like
        #   prompts * log(acq_model.forward(self.x)) - self.x * sensitivity
        return 0


submission_callbacks = [MaxIteration(660)]
