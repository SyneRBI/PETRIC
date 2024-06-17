"""Usage in notebook.ipynb:
from main import Submission, submission_callbacks
from cil.optimisation.utilities import callbacks

data = "TODO"
metrics = [callbacks.ProgressCallback()]

algorithm = Submission(data)
algorithm.run(np.inf, callbacks=metrics + submission_callbacks)
"""
from cil.optimisation.algorithms import GD
from cil.optimisation.utilities.callbacks import Callback

class EarlyStopping(Callback):
    def __call__(self, algorithm):
        if algorithm.x <= -15:  # arbitrary stopping criterion
            raise StopIteration

submission_callbacks = [EarlyStopping()]

class Submission(GD):
    def __init__(self, data, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Your code here
        self.data = data

    def update(self):
        # Your code here
        return super().update()
