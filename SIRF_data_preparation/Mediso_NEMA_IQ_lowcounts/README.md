# Mediso_NEMA_IQ_lowcounts
Aside from usual steps

##
Copy VOIs from high count data, but with adjustement of size. KT
did this via STIR utilities (but can be done via SIRF as well)
```
for f in VOI*.hv; do
    zoom_image --template data/Mediso_NEMA_IQ_lowcounts/OSEM_image.hv data/Mediso_NEMA_IQ_lowcounts/$f $f;
done
```
## BSREM
Given large oscillations with subsets, I reduced the number of subsets from 12 to 6 (in `dataset_settings.py`) but increased the initial step size.
```
python -m SIRF_data_preparation.get_penalisation_factor  --dataset=Mediso_NEMA_IQ_lowcounts --ref_dataset=Mediso_NEMA_IQ -w
python -m SIRF_data_preparation.run_BSREM Mediso_NEMA_IQ_lowcounts --initial_step_size=.5 --relaxation_eta=.0105
```