"""
Some utilities for plotting objectives and metrics
"""
import csv
import os
import numpy
from typing import Iterator
import matplotlib.pyplot as plt
from petric import QualityMetrics
import sirf.STIR as STIR

def read_objectives(datadir='.') -> numpy.array:
    """Reads objectives.csv and returns as 2d array"""
    with open(os.path.join(datadir, 'objectives.csv'), newline='') as csvfile:
        reader = csv.reader(csvfile)
        next(reader) # skip first line
        objs = numpy.array([(float(row[0]), float(row[1])) for row in reader])
        return objs


def get_metrics(qm: QualityMetrics, iters: Iterator, srcdir='.') -> numpy.array :
    """Read 'iter*.hv' images from datadir, compute metrics and return as 2d array"""
    m = []
    for iter in iters:
        im = STIR.ImageData(os.path.join(srcdir,f"iter_{iter:04d}.hv"))
        m.append([*qm.evaluate(im).values()])
    return numpy.array(m)
#%%
def plot_metrics(iters: Iterator, m: numpy.array, labels=[], suffix=""):
    """Make 2 subplots of metrics"""
    ax = plt.subplot(121)
    plt.plot(iters, m[:,0], label=labels[0]+suffix)
    plt.plot(iters, m[:,1], label=labels[1]+suffix)
    ax.legend()
    ax = plt.subplot(122)
    for i in range(2, m.shape[1]):
        plt.plot(iters, m[:,i], label=labels[i]+suffix)
    ax.legend()
