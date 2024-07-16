#%%
from petric import MetricsWithTimeout, get_data, SRCDIR
import main_OSEM
import SIRF_data_preparation.data_QC as data_QC
import matplotlib.pyplot as plt
#%%
outdir="./output/OSEM_Siemens_mMR_NEMA_IQ"
data = get_data(srcdir="./data/Siemens_mMR_NEMA_IQ/", outdir=outdir)
#%%
num_subsets = 7
algo = main_OSEM.Submission(data, num_subsets, update_objective_interval=20)
#%%
algo.run(500, callbacks=[MetricsWithTimeout(transverse_slice=72, coronal_slice=109, seconds=500, outdir=outdir)])
data_QC.plot_image(algo.get_output(),transverse_slice=72, coronal_slice=109)
plt.show()