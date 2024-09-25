# Torso phantom scanned on a GE Discovery MI (3 ring)

This data is from a scan performed by GE of the
Data Spectrum [Antropomorphic Torso Phantom](https://www.spect.com/pdf/anthropomorphic-torso-phantom.pdf)
with additional lesion inserts of diameter 10mm.

Activity ratio between "liver" and "torso" is approximately 2. Lungs
are empty (air). Contrast of the lesions is unfortunately unknown.

"Corrections" were obtained with GE Duetto and converted to STIR Interfile
using internal scripts.

Due to data size issues and count levels, the supplied data is **reduced** from the original scan
by keeping only the "direct" sinograms (segment 0, corresponding to min/max ring differences -1/+1), e.g. on the command line
```
SSRB prompts.hs prompts_f1b1.hs 1 1 0 0 1
```

In addition, as current PETRIC examples do not cope with non-TOF multfactors for TOF data, the
multfactors were expanded to TOF (by duplication).

## VOIs

VOIs were determined by Kris Thielemans on reconstructed images and approximately placed
where some of the lesions are visible. They are not necessarily at the correct location.
