"""Some utilities for plotting objectives and metrics."""
import csv
from pathlib import Path
from typing import Iterator

import matplotlib.pyplot as plt
import numpy as np

import sirf.STIR as STIR
from petric import QualityMetrics


def read_objectives(datadir='.'):
    """Reads objectives.csv and returns as 2d array"""
    with (Path(datadir) / 'objectives.csv').open() as csvfile:
        reader = csv.reader(csvfile)
        next(reader) # skip first (header) line
        return np.asarray([tuple(map(float, row)) for row in reader])


def get_metrics(qm: QualityMetrics, iters: Iterator[int], srcdir='.'):
    """Read 'iter_{iter_glob}.hv' images from datadir, compute metrics and return as 2d array"""
    return np.asarray([
        list(qm.evaluate(STIR.ImageData(str(Path(srcdir) / f'iter_{i:04d}.hv'))).values()) for i in iters])


def pass_index(metrics: np.ndarray, thresh: np.ndarray, window: int = 1) -> int:
    """
    Returns first index of `metrics` with value <= `thresh`.
    The value must remain below the threshold for at least `window`.
    Raises IndexError if doesn't pass.
    """
    assert metrics.shape[1] == len(thresh)
    assert metrics.ndim == 2
    assert thresh.ndim == 1

    m = (metrics <= thresh[None]).all(1)
    assert window == 1
    return np.where(m[1:] & m[:-1])[0][0]


def plot_metrics(iters: Iterator[int], m: np.ndarray, labels=None, suffix=""):
    """Make 2 subplots of metrics"""
    if labels is None:
        labels = [""] * m.shape[1]
    ax = plt.subplot(121)
    plt.plot(iters, m[:, 0], label=labels[0] + suffix)
    plt.plot(iters, m[:, 1], label=labels[1] + suffix)
    ax.legend()
    ax = plt.subplot(122)
    for i in range(2, m.shape[1]):
        plt.plot(iters, m[:, i], label=labels[i] + suffix)
    ax.legend()
