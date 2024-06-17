# SyneRBI Challenge

## TL;DR

The organisers will execute:

```python
from main import Submission, submission_callbacks
assert issubclass(Submission, cil.optimisation.algorithms.Algorithm)
with Timeout(minutes=5):
    Submission(data).run(np.inf, callbacks=metrics + submission_callbacks)
```

> [!WARNING]
> To avoid timing out, please disable any debugging/plotting code before submitting!

The organisers will have private versions of `data` and `metrics`.
Smaller test (public) versions of `data` and `metrics` are defined in the [`notebook.ipynb`](notebook.ipynb).

## Layout

Only [`main.py`](main.py) is required.
[SIRF](https://github.com/SyneRBI/SIRF), [CIL](https://github.com/TomographicImaging/CIL), and CUDA are already installed.
Additional dependencies may be specified via `apt.txt`, `environment.yml`, and/or `requirements.txt`.

- (required) `main.py`: must define a `class Submission(cil.optimisation.algorithms.Algorithm)`
- `notebook.ipynb`: can be used for experimenting. Runs `main.Submission()` on test `data` with basic `metrics`
- `apt.txt`: passed to `apt install`
- `environment.yml`: passed to `conda install`
- `requirements.txt`: passed to `pip install`
