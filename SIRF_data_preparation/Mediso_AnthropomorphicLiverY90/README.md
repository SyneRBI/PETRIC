# Data from the Mediso AnyScan at NPL
Initial processing steps
```sh
 cd ~/devel/PETRIC/orgdata/
 wget https://nplanywhere.npl.co.uk/userportal/?v=4.6.1#/shared/public/nrKe5vWynvyMsp7m/e9e3d4b8-8f83-47be-bf2d-17a96a7a8aac
 unzip MedisoAnthropomorphicLiverPhantom.zip
 cd ../data
 mkdir -p  MedisoAnthropomorphicLiverY90
 cd MedisoAnthropomorphicLiverY90/
 cp -rp ../orgdata/MedisoAnthropomorphicLiverY90/sinograms/* .
 mkdir PETRIC
 cp -rp ../orgdata/MedisoAnthropomorphicLiverY90/VOIs/* PETRIC
 cp -rp ../orgdata/MedisoAnthropomorphicLiverY90/README.md .
 python ../../SIRF_data_preparation/create_initial_images.py --template_image=PETRIC/VOI_whole_object.hv .
 ```
 I needed to fix the OSEM header (manual):
 ```
 !imaging modality := PT
 radionuclide name[1] := ^90^Yttrium
 radionuclide halflife (sec)[1] := 230550
 radionuclide branching factor[1] := 3.19e-05
 ```
