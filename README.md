# SyneRBI Challenge

The organisers will execute:

```python
test = main.Test("/some/private/input_patients_dir")
with Timeout(minutes=5):
    test.run_all_patients("/some/private/output_patients_dir")
evaluate_metrics("/some/private/output_patients_dir")
```

To avoid timing out, please disable any debugging/plotting code before submitting!

Layout:

- /challenge/
  - input_patients_dir/
    - patient_01/
      - sinogram.npy
      - reference.npy
    - patient_02/
    - ...
  - output_patients_dir/
    - patient_01/
      - 000.npy
      - 001.npy
      - ...

Private (organiser) test machine:

- /$JOB_ID/
  - input_patients_dir/
    - patient_01/
      - sinogram.npy
  - output_patients_dir/
    - patient_01/
      - 000.npy
- /hidden/patients/reference/dir/
  - patient_01/
    - reference.npy
