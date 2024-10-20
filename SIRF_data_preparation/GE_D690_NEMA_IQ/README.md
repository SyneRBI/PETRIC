# Preparation steps for NEMA IQ data scanned on GE Discovery 690
## Reference solution
```sh
python -m SIRF_data_preparation.run_BSREM GE_D690_NEMA_IQ  --updates=500 --initial_step_size=1 --interval=10 --outreldir=BSREM1
python -m SIRF_data_preparation.run_BSREM GE_D690_NEMA_IQ --updates=7520 --initial_step_size=.8 --relaxation_eta=.01  --num_subsets=6 --initial_image=output/GE_D690_NEMA_IQ/BSREM1/iter_final.hv --outreldir=BSREM2
python -m SIRF_data_preparation.run_BSREM GE_D690_NEMA_IQ --updates=1000 --initial_step_size=.2 --relaxation_eta=.01  --num_subsets=1 --initial_image=output/GE_D690_NEMA_IQ/BSREM2/iter_7520.hv --outreldir=BSREM3 --interval=2
```
## VOIs
```sh
python -m SIRF_data_preparation.create_NEMA_IQ_VOIs --dataset=GE_D690_NEMA_IQ --central_VOI=False --angle_smallest_sphere=30 --spheres="(2,3,5)"
```
