from cil.optimisation.algorithms import GD

class Submission(GD):
    def __init__(self, data, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Your code here
        self.data = data

    def update(self):
        # Your code here
        return super().update()
