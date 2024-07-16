from petric import MetricsWithTimeout, get_data, SRCDIR
from sirf.contrib.BSREM.BSREM import BSREM1
from sirf.contrib.partitioner import partitioner

scanID = "NeuroLF_Hoffman_Dataset"
if scanID == 'Siemens_mMR_NEMA_IQ':
    slices = { 'transverse_slice': 72, 'coronal_slice': 109} #, 'sagittal_slice': 89}
    num_subsets = 7
elif scanID == 'NeuroLF_Hoffman_Dataset':
    slices = { 'transverse_slice': 72}
    num_subsets = 16
else:
    slices = {}
    # Vision
    num_subsets = 5

outdir="./output/BSREM_" + scanID
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
#%%
algo.run(15000, callbacks=[MetricsWithTimeout(**slices, outdir=outdir, seconds=3600*100)])
