from pathlib import Path, PurePath

import numpy as np
from tqdm import trange


class PatientData:
    def __init__(self, patient_dir: PurePath):
        self.patient_dir = Path(patient_dir)
        self.sinogram = np.random.random((252, 344, 344)) # TODO
        self.image_size = (127, 344, 344) # TODO
        self.image_reference = np.random.random(self.image_size) # TODO


class Test:
    def __init__(self, input_patients_dir: PurePath):
        self.input_patients_dir = Path(input_patients_dir)

    def run_all_patients(self, output_patients_dir: PurePath | None = None):
        for input_dir in self.input_patients_dir.glob("*/"):
            output_dir = Path(output_patients_dir) / input_dir.name if output_patients_dir else None
            self.run(input_dir, output_dir=output_dir)

    def run(self, input_dir: PurePath, output_dir: PurePath | None = None, max_iterations=100):
        data = PatientData(input_dir)
        img = np.ones(data.image_size)
        with trange(max_iterations) as t:
            for iter in t:
                img = self.reconstruct(data.sinogram, img)
                if output_dir:
                    np.save(Path(output_dir) / f"{iter:03d}.npy", img)
                nrmse = (((img - data.image_reference) ** 2).sum() / (data.image_reference ** 2).sum()) ** 0.5
                t.set_postfix(nrmse=nrmse, refresh=False)

    def reconstruct(self, sinogram: np.ndarray, image: np.ndarray) -> np.ndarray:
        raise NotImplementedError("""TODO: write your code for 1 iteration here, e.g.
            return image * backward(sinogram / (forward(image) + randoms_and_scatter)) / backward(np.ones_like(image))
        """)


if __name__ == "__main__":
    test = Test("input_patients_dir")
    test.run_all_patients("output_patients_dir")
