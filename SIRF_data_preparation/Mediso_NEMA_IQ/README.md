# Data from the Mediso AnyScan at NPL
Initial processing steps
```sh
orgpath=/mnt/share/petric-wip/NEMA_Challenge
#orgpath=~/devel/PETRIC/orgdata/
# cd $orgpath
#wget https://nplanywhere.npl.co.uk/userportal/?v=4.6.1#/shared/public/nrKe5vWynvyMsp7m/e9e3d4b8-8f83-47be-bf2d-17a96a7a8aac
#unzip NEMA_Challenge.zip
cd ~/devel/PETRIC/data
mkdir -p  Mediso_NEMA_IQ
cd Mediso_NEMA_IQ/
# trim sinograms to avoid "corner" problems in mult_factors
# TODO for next data: use 30 (as some problems remain)
for f in additive_term.hs  mult_factors.hs  prompts.hs; do
   SSRB -t 20 $f $orgpath/sinograms/$f
done
# alternative if we don't need to trim
#cp -rp $orgpath/sinograms/* .
# get rid of NaNs
python prepare.py
# now handle VOIs
mkdir PETRIC
cp -rp $orgpath/VOIs/* PETRIC
# cp -rp $orgpath/README.md .
cd PETRIC
stir_math VOI_background.hv VOI_backgroung.hv
rm VOI_backgroung.*
rm *ahv
cd ..
python ../../SIRF_data_preparation/create_initial_images.py --template_image=PETRIC/VOI_whole_object.hv .
 ```
 I needed to fix the OSEM header (manual):
 ```
 !imaging modality := PT
 ```
python ../../SIRF_data_preparation/data_QC
