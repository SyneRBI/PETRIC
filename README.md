# PETRIC: PET Rapid Image reconstruction Challenge

[![website](https://img.shields.io/badge/announcement-website-purple?logo=workplace&logoColor=white)](https://www.ccpsynerbi.ac.uk/events/petric/)
[![wiki](https://img.shields.io/badge/details-wiki-blue?logo=googledocs&logoColor=white)](https://github.com/SyneRBI/PETRIC/wiki)
[![register](https://img.shields.io/badge/participate-register-green?logo=ticktick&logoColor=white)](https://github.com/SyneRBI/PETRIC/issues/new/choose)
[![leaderboard](https://img.shields.io/badge/rankings-leaderboard-orange?logo=tensorflow&logoColor=white)](https://petric.tomography.stfc.ac.uk/leaderboard)
[![discord](https://img.shields.io/badge/chat-discord-blue?logo=discord&logoColor=white)](https://discord.gg/Ayd72Aa4ry)

## Participating

The organisers will provide GPU-enabled cloud runners which have access to larger private datasets for evaluation. To gain access, you must [register](https://github.com/SyneRBI/PETRIC/issues/new/choose). The organisers will then create a private team submission repository for you.

## Layout

Only [`main.py`](main.py) is required.
[SIRF](https://github.com/SyneRBI/SIRF), [CIL](https://github.com/TomographicImaging/CIL), and CUDA are already installed (using [synerbi/sirf:latest-gpu](https://github.com/synerbi/SIRF-SuperBuild/pkgs/container/sirf)).
Additional dependencies may be specified via `apt.txt`, `environment.yml`, and/or `requirements.txt`.

- (required) `main.py`: must define a `class Submission(cil.optimisation.algorithms.Algorithm)`
- `notebook.ipynb`: can be used for experimenting. Runs `main.Submission()` on test `data` with basic `metrics`
- `apt.txt`: passed to `apt install`
- `environment.yml`: passed to `conda install`
- `requirements.txt`: passed to `pip install`

## Organiser setup

The organisers will execute:

```python
from main import Submission, submission_callbacks
assert issubclass(Submission, cil.optimisation.algorithms.Algorithm)
with Timeout(minutes=5):
    Submission(data).run(np.inf, callbacks=metrics + submission_callbacks)
```

> [!WARNING]
> To avoid timing out, please disable any debugging/plotting code before submitting!
> This includes removing any progress/logging from `submission_callbacks`.

The organisers will have private versions of `data` and `metrics`.
Smaller test (public) versions of `data` and `metrics` are defined in the [`notebook.ipynb`](notebook.ipynb).
