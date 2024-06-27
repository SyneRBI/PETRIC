from petric import get_data, MetricsWithTimeout
from sirf.contrib.BSREM.BSREM import BSREM1

data = get_data(num_subsets=7, srcdir="./data/Siemens_mMR_NEMA_IQ", outdir="./output/BSREM_mMR_NEMA_IQ")
algo = BSREM1(data.data, data.obj_funs, initial=data.OSEM_image, initial_step_size=.3, relaxation_eta=.01, update_objective_interval=10)
algo.run(5000, callbacks=[MetricsWithTimeout(transverse_slice=72, coronal_slice=109)])
