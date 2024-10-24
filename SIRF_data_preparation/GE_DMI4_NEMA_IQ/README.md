# GE_DMI4_NEMA_IQ

```
python3 -m SIRF_data_preparation.create_initial_images data/GE_DMI4_NEMA_IQ -t None -s 211
python3 -m SIRF_data_preparation.create_NEMA_IQ_VOIs --central_VOI=0 --dataset=GE_DMI4_NEMA_IQ --angle_smallest_sphere=30 --spheres='(2,3,4)'
```
