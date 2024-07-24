# PETRIC: PET Rapid Image reconstruction Challenge

[![website](https://img.shields.io/badge/announcement-website-purple?logo=workplace&logoColor=white)](https://www.ccpsynerbi.ac.uk/events/petric/)
[![wiki](https://img.shields.io/badge/details-wiki-blue?logo=googledocs&logoColor=white)](https://github.com/SyneRBI/PETRIC/wiki)
[![register](https://img.shields.io/badge/participate-register-green?logo=ticktick&logoColor=white)](https://github.com/SyneRBI/PETRIC/issues/new/choose)
[![leaderboard](https://img.shields.io/badge/rankings-leaderboard-orange?logo=tensorflow&logoColor=white)](https://petric.tomography.stfc.ac.uk/leaderboard)
[![discord](https://img.shields.io/badge/chat-discord-blue?logo=discord&logoColor=white)](https://discord.gg/Ayd72Aa4ry)

## Participating

The organisers will provide GPU-enabled cloud runners which have access to larger private datasets for evaluation. To gain access, you must [register](https://github.com/SyneRBI/PETRIC/issues/new/choose). The organisers will then create a private team submission repository for you.

## Layout

The organisers will import your submitted algorithm from `main.py` and then run & evaluate it.
Please create this file! See the example `main_*.py` files for inspiration.

[SIRF](https://github.com/SyneRBI/SIRF), [CIL](https://github.com/TomographicImaging/CIL), and CUDA are already installed (using [synerbi/sirf](https://github.com/synerbi/SIRF-SuperBuild/pkgs/container/sirf)).
Additional dependencies may be specified via `apt.txt`, `environment.yml`, and/or `requirements.txt`.

- (required) `main.py`: must define a `class Submission(cil.optimisation.algorithms.Algorithm)` and a list of `submission_callbacks`
- `apt.txt`: passed to `apt install`
- `environment.yml`: passed to `conda install`
- `requirements.txt`: passed to `pip install`

You can also find some example notebooks here which should help you with your development:
- https://github.com/SyneRBI/SIRF-Contribs/blob/master/src/notebooks/BSREM_illustration.ipynb

## Organiser setup

The organisers will execute (after downloading https://petric.tomography.stfc.ac.uk/data/ to `/path/to/data`):

```sh
docker run --rm -it -v /path/to/data:/mnt/share/petric:ro -v .:/workdir -w /workdir --gpus all synerbi/sirf:edge-gpu /bin/bash
# ... or ideally synerbi/sirf:latest-gpu after the next SIRF release!
pip install git+https://github.com/TomographicImaging/Hackathon-000-Stochastic-QualityMetrics
# ... conda/pip/apt install environment.yml/requirements.txt/apt.txt
python petric.py
```

> [!TIP]
> `petric.py` will effectively execute:
>
> ```python
> from main import Submission, submission_callbacks  # your submission
> from petric import data, metrics  # our data & evaluation
> assert issubclass(Submission, cil.optimisation.algorithms.Algorithm)
> Submission(data).run(numpy.inf, callbacks=metrics + submission_callbacks)
> ```

<!-- br -->

> [!WARNING]
> To avoid timing out (currently 10 min runtime, will likely be increased a bit for the final evaluation after submissions close), please disable any debugging/plotting code before submitting!
> This includes removing any progress/logging from `submission_callbacks`.

- `data` to test/train your `Algorithm`s is available at https://petric.tomography.stfc.ac.uk/data/ and is likely to grow (more info to follow soon)
  + fewer datasets will be used by the organisers to provide a temporary [leaderboard](https://petric.tomography.stfc.ac.uk/leaderboard)
  + please contact us if you'd like to contribute your own public datasets!
- `metrics` are calculated by `class QualityMetrics` within `petric.py`

Any modifications to `petric.py` are ignored.
