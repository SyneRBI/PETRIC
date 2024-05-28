import os
import data_preparation_setup
from data_preparation_setup import repo_directory

from sirf.Utilities import examples_data_path
from sirf_exercises import exercises_data_path

data_path = exercises_data_path('PET', 'mMR', 'NEMA_IQ')
challenge_data_path = os.path.join(repo_directory, 'data')

print(data_path)
print(challenge_data_path)

