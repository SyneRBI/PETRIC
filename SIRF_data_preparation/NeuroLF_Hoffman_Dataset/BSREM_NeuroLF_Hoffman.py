from petric import SRCDIR, MetricsWithTimeout, get_data
from sirf.contrib.BSREM.BSREM import BSREM1
from sirf.contrib.partitioner import partitioner
from SIRF_data_preparation.dataset_settings import get_settings

scanID = "NeuroLF_Hoffman_Dataset"
settings = get_settings(scanID)
slices = settings.slices
num_subsets = settings.num_subsets
outdir = f"./output/{scanID}/BSREM"
outdir1 = f"./output/{scanID}/BSREM_cont"

data = get_data(srcdir=SRCDIR / scanID, outdir=outdir)
data_sub, acq_models, obj_funs = partitioner.data_partition(data.acquired_data, data.additive_term, data.mult_factors,
                                                            num_subsets, initial_image=data.OSEM_image)
# WARNING: modifies prior strength with 1/num_subsets (as currently needed for BSREM implementations)
data.prior.set_penalisation_factor(data.prior.get_penalisation_factor() / len(obj_funs))
data.prior.set_up(data.OSEM_image)
for f in obj_funs: # add prior evenly to every objective function
    f.set_prior(data.prior)

algo = BSREM1(data_sub, obj_funs, initial=data.OSEM_image, initial_step_size=.3, relaxation_eta=.01,
              update_objective_interval=80)
# %%
algo.run(15000, callbacks=[MetricsWithTimeout(**slices, outdir=outdir, seconds=3600 * 100)])
