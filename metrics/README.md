# Reconstruction with calculation of metrics

## Requirements

- CIL with callbacks https://github.com/TomographicImaging/CIL/pull/1659
- metrics from Stochastic Hackathon Quality Metrics, branch [`cil_callback`](https://github.com/TomographicImaging/Hackathon-000-Stochastic-QualityMetrics/tree/cil_callback)

### Installation

Currently building from this SuperBuild branch https://github.com/SyneRBI/SIRF-SuperBuild/pull/718

```bash

docker/compose.sh -dgb -- --build-arg EXTRA_BUILD_FLAGS='-DGadgetron_TAG=6202fb7352a14fb82817b57a97d928c988eb0f4b -DISMRMRD_TAG=v1.13.7 -Dsiemens_to_ismrmrd_TAG=v1.2.11 -DDEVEL_BUILD=ON -DBUILD_CIL=ON -DCCPi-Regularisation-Toolkit_TAG=origin/master' --build-arg RUN_CTEST=0

```
where `-dgb` tells to `b`uild the `g`pu and `d`evelopment branches. The whole lot of flags can be checked [here](https://github.com/SyneRBI/SIRF-SuperBuild/blob/c21a2a45591550a6e257fc6f3dc343294b2c3127/docker/compose.sh#L24-L31)

```
  h) print_help; exit 0 ;; # print this help
  b) build=1 ;; # build
  r) run=1 ;; # run
  d) devel=1 ;; # use development (main/master) repo branches
  c) cpu=1 ;; # enable CPU
  g) gpu=1 ;; # enable GPU
  U) update_ccache=0 ;; # disable updating docker/devel/.ccache
  R) regen_ccache=1 ;; # regenerate (rather than append to) docker/devel/.ccache (always true if both -c and -g are specified)
```


## Metrics