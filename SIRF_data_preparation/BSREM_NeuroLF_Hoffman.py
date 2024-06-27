from petric import MetricsWithTimeout, get_data
from sirf.contrib.BSREM.BSREM import BSREM1
from sirf.contrib.partitioner import partitioner

data = get_data(srcdir="./data/NeuroLF_Hoffman_Dataset", outdir="./output/BSREM_NeuroLF_Hoffman")
num_subsets = 16
data_sub, acq_models, obj_funs = partitioner.data_partition(data.acquired_data, data.additive_term, data.mult_factors,
                                                            num_subsets, initial_image=data.OSEM_image)
# WARNING: modifies prior strength with 1/num_subsets (as currently needed for BSREM implementations)
data.prior.set_penalisation_factor(data.prior.get_penalisation_factor() / len(obj_funs))
data.prior.set_up(data.OSEM_image)
for f in obj_funs: # add prior evenly to every objective function
    f.set_prior(data.prior)

algo = BSREM1(data_sub, obj_funs, initial=data.OSEM_image, initial_step_size=.3, relaxation_eta=.01,
              update_objective_interval=10)
algo.run(5000, callbacks=[MetricsWithTimeout(transverse_slice=72)])
