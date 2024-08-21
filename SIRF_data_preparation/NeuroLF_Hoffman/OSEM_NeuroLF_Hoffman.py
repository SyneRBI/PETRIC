#%%
import sys
sys.path.append('/home/kris/devel/PETRIC')
import os
os.chdir('/home/kris/devel/PETRIC')
#%%
from petric import MetricsWithTimeout, get_data, SRCDIR
import main_OSEM
import SIRF_data_preparation.data_QC as data_QC
import matplotlib.pyplot as plt
#%%
#%%
outdir="./output/OSEM_mNeuroLF_Hoffman_Dataset"
data = get_data(srcdir="./data/NeuroLF_Hoffman_Dataset/", outdir=outdir)
#%%
slices={}
num_subsets = 16
algo = main_OSEM.Submission(data, num_subsets, update_objective_interval=20)
#%%
algo.run(600, callbacks=[MetricsWithTimeout(**slices, seconds=50000, outdir=outdir)])
data_QC.plot_image(algo.get_output(), **slices)
plt.show()
# %%
