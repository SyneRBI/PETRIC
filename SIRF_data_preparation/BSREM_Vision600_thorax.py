from petric import get_data, MetricsWithTimeout
from sirf.contrib.BSREM.BSREM import BSREM1

data = get_data(num_subsets=5, srcdir="./data/Siemens_Vision600_thorax", outdir="./output/BSREM_Vision600_thorax")
algo = BSREM1(data.data, data.obj_funs, initial=data.OSEM_image, initial_step_size=.3, relaxation_eta=.01, update_objective_interval=10)
algo.run(5000, callbacks=[MetricsWithTimeout()])
