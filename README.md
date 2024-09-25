# PETRIC: PET Rapid Image reconstruction Challenge

[![website](https://img.shields.io/badge/announcement-website-purple?logo=workplace&logoColor=white)](https://www.ccpsynerbi.ac.uk/events/petric/)
[![wiki](https://img.shields.io/badge/details-wiki-blue?logo=googledocs&logoColor=white)][wiki]
[![register](https://img.shields.io/badge/participate-register-green?logo=ticktick&logoColor=white)][register]
[![leaderboard](https://img.shields.io/badge/rankings-leaderboard-orange?logo=tensorflow&logoColor=white)][leaderboard]
[![discord](https://img.shields.io/badge/chat-discord-blue?logo=discord&logoColor=white)](https://discord.gg/Ayd72Aa4ry)

## Participating

The organisers will provide GPU-enabled cloud runners which have access to larger private datasets for evaluation. To gain access, you must [register]. The organisers will then create a private team submission repository for you.

[register]: https://github.com/SyneRBI/PETRIC/issues/new/choose

## Layout

The organisers will import your submitted algorithm from `main.py` and then run & evaluate it.
Please create this file! See the example `main_*.py` files for inspiration.

[SIRF](https://github.com/SyneRBI/SIRF), [CIL](https://github.com/TomographicImaging/CIL), and CUDA are already installed (using [synerbi/sirf](https://github.com/synerbi/SIRF-SuperBuild/pkgs/container/sirf)).
Additional dependencies may be specified via `apt.txt`, `environment.yml`, and/or `requirements.txt`.

- (required) `main.py`: must define a `class Submission(cil.optimisation.algorithms.Algorithm)` and a (potentially empty) list of `submission_callbacks`, e.g.:
  + [main_BSREM.py](main_BSREM.py)
  + [main_ISTA.py](main_ISTA.py)
  + [main_OSEM.py](main_OSEM.py)
- `apt.txt`: passed to `apt install`
- `environment.yml`: passed to `conda install`, e.g.:

  ```yml
  name: winning-submission
  channels: [conda-forge, nvidia]
  dependencies:
  - cupy
  - cuda-version =11.8
  - pip
  - pip:
    - git+https://github.com/MyResearchGroup/prize-winning-algos
  ```

- `requirements.txt`: passed to `pip install`, e.g.:

  ```txt
  cupy-cuda11x
  git+https://github.com/MyResearchGroup/prize-winning-algos
  ```

> [!TIP]
> You probably should create either an `environment.yml` or `requirements.txt` file (but not both).

You can also find some example notebooks here which should help you with your development:
- https://github.com/SyneRBI/SIRF-Contribs/blob/master/src/notebooks/BSREM_illustration.ipynb

## Organiser setup

The organisers will execute (after installing [nvidia-docker](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html) & downloading <https://petric.tomography.stfc.ac.uk/data/> to `/path/to/data`):

<!-- TODO: use synerbi/sirf:latest-gpu after the next SIRF release -->

```sh
# 1. git clone & cd to your submission repository
# 2. mount `.` to container `/workdir`:
docker run --rm -it --gpus all -p 6006:6006 \
  -v /path/to/data:/mnt/share/petric:ro \
  -v .:/workdir -w /workdir synerbi/sirf:edge-gpu /bin/bash
# 3. install metrics & GPU libraries
conda install monai tensorboard tensorboardx jupytext cudatoolkit=11.8
pip uninstall torch # monai installs pytorch (CPU), so remove it
pip install tensorflow[and-cuda]==2.14  # last to support cu118
pip install torch --index-url https://download.pytorch.org/whl/cu118
pip install git+https://github.com/TomographicImaging/Hackathon-000-Stochastic-QualityMetrics
# 4. optionally, conda/pip/apt install environment.yml/requirements.txt/apt.txt
# 5. run your submission
python petric.py &
# 6. optionally, serve logs at <http://localhost:6006>
tensorboard --bind_all --port 6006 --logdir ./output
```

## FAQ

See the [wiki/Home][wiki] and [wiki/FAQ](https://github.com/SyneRBI/PETRIC/wiki/FAQ) for more info.

> [!TIP]
> `petric.py` will effectively execute:
>
> ```python
> from main import Submission, submission_callbacks  # your submission (`main.py`)
> from petric import data, metrics  # our data & evaluation
> assert issubclass(Submission, cil.optimisation.algorithms.Algorithm)
> Submission(data).run(numpy.inf, callbacks=metrics + submission_callbacks)
> ```

<!-- br -->

> [!WARNING]
> To avoid timing out (currently 10 min runtime, will likely be increased a bit for the final evaluation after submissions close), please disable any debugging/plotting code before submitting!
> This includes removing any progress/logging from `submission_callbacks` and any debugging from `Submission.__init__`.

- `data` to test/train your `Algorithm`s is available at <https://petric.tomography.stfc.ac.uk/data/> and is likely to grow (more info to follow soon)
  + fewer datasets will be available during the submission phase, but more will be available for the final evaluation after submissions close
  + please contact us if you'd like to contribute your own public datasets!
- `metrics` are calculated by `class QualityMetrics` within `petric.py`
  + this does not contribute to your runtime limit
  + effectively, only `Submission(data).run(np.inf, callbacks=submission_callbacks)` is timed
- when using the temporary [leaderboard], it is best to:
  + change `Horizontal Axis` to `Relative`
  + untick `Ignore outliers in chart scaling`
  + see [the wiki](https://github.com/SyneRBI/PETRIC/wiki#metrics-and-thresholds) for details

Any modifications to `petric.py` are ignored.

[wiki]: https://github.com/SyneRBI/PETRIC/wiki
[leaderboard]: https://petric.tomography.stfc.ac.uk/leaderboard/?smoothing=0#timeseries&_smoothingWeight=0
