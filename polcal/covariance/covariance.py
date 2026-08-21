import sys
import os
from dotenv import load_dotenv
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'utilities')))
import read_image
import numpy as np
from tqdm import tqdm
import time
import torch
import torch.nn.functional as F

load_dotenv()
work_dir = os.getenv('covariance_file_path')
if not os.path.exists(work_dir): 
    os.makedirs(work_dir)

def set_padding(input_array, x_window_size, y_window_size):
    pad_x = (x_window_size - 1) // 2
    pad_y = (y_window_size - 1) // 2
    padded_tensor = F.pad(torch.tensor(input_array), (pad_y, pad_y, pad_x, pad_x), mode='constant', value=0)
    return padded_tensor.numpy()

def compute_covariance_matrix(HH, HV, VH, VV):
    rows, cols = HH.shape
    
    # Initialize 16 output arrays to store covariance matrix elements
    C11 = np.zeros((rows, cols), dtype=np.complex128)
    C12 = np.zeros((rows, cols), dtype=np.complex128)
    C13 = np.zeros((rows, cols), dtype=np.complex128)
    C14 = np.zeros((rows, cols), dtype=np.complex128)
    C21 = np.zeros((rows, cols), dtype=np.complex128)
    C22 = np.zeros((rows, cols), dtype=np.complex128)
    C23 = np.zeros((rows, cols), dtype=np.complex128)
    C24 = np.zeros((rows, cols), dtype=np.complex128)
    C31 = np.zeros((rows, cols), dtype=np.complex128)
    C32 = np.zeros((rows, cols), dtype=np.complex128)
    C33 = np.zeros((rows, cols), dtype=np.complex128)
    C34 = np.zeros((rows, cols), dtype=np.complex128)
    C41 = np.zeros((rows, cols), dtype=np.complex128)
    C42 = np.zeros((rows, cols), dtype=np.complex128)
    C43 = np.zeros((rows, cols), dtype=np.complex128)
    C44 = np.zeros((rows, cols), dtype=np.complex128)

    # Loop over each pixel and compute the covariance matrix
    with tqdm(total=rows * cols, desc="Computing covariance matrices", unit = ' pixels') as pbar:
        for i in range(rows):
            for j in range(cols):
                scattering_matrix = np.array([[HH[i, j], HV[i, j]], [VH[i, j], VV[i, j]]])
                scattering_vector = scattering_matrix.flatten()
                covariance_matrix = np.outer(scattering_vector, scattering_vector.conj())
                
                # Store each element of the 4x4 covariance matrix in the corresponding array
                C11[i, j] = covariance_matrix[0, 0]
                C12[i, j] = covariance_matrix[0, 1]
                C13[i, j] = covariance_matrix[0, 2]
                C14[i, j] = covariance_matrix[0, 3]
                C21[i, j] = covariance_matrix[1, 0]
                C22[i, j] = covariance_matrix[1, 1]
                C23[i, j] = covariance_matrix[1, 2]
                C24[i, j] = covariance_matrix[1, 3]
                C31[i, j] = covariance_matrix[2, 0]
                C32[i, j] = covariance_matrix[2, 1]
                C33[i, j] = covariance_matrix[2, 2]
                C34[i, j] = covariance_matrix[2, 3]
                C41[i, j] = covariance_matrix[3, 0]
                C42[i, j] = covariance_matrix[3, 1]
                C43[i, j] = covariance_matrix[3, 2]
                C44[i, j] = covariance_matrix[3, 3]
                
                pbar.update(1)

    # Save each output array as a .npy file
    np.save(os.path.join(work_dir, 'C11.npy'), C11)
    np.save(os.path.join(work_dir, 'C12.npy'), C12)
    np.save(os.path.join(work_dir, 'C13.npy'), C13)
    np.save(os.path.join(work_dir, 'C14.npy'), C14)
    np.save(os.path.join(work_dir, 'C21.npy'), C21)
    np.save(os.path.join(work_dir, 'C22.npy'), C22)
    np.save(os.path.join(work_dir, 'C23.npy'), C23)
    np.save(os.path.join(work_dir, 'C24.npy'), C24)
    np.save(os.path.join(work_dir, 'C31.npy'), C31)
    np.save(os.path.join(work_dir, 'C32.npy'), C32)
    np.save(os.path.join(work_dir, 'C33.npy'), C33)
    np.save(os.path.join(work_dir, 'C34.npy'), C34)
    np.save(os.path.join(work_dir, 'C41.npy'), C41)
    np.save(os.path.join(work_dir, 'C42.npy'), C42)
    np.save(os.path.join(work_dir, 'C43.npy'), C43)
    np.save(os.path.join(work_dir, 'C44.npy'), C44)

    del C11 
    del C12 
    del C13 
    del C14 
    del C21
    del C22
    del C23
    del C24
    del C31
    del C32
    del C33
    del C34
    del C41
    del C42
    del C43
    del C44

if __name__ == "__main__":
    # Example usage
    HH = set_padding(read_image.image_array(os.getenv('HH_tif_path')), x_window_size = 201, y_window_size = 201)
    HV = set_padding(read_image.image_array(os.getenv('HV_tif_path')), x_window_size = 201, y_window_size = 201)
    VH = set_padding(read_image.image_array(os.getenv('VH_tif_path')), x_window_size = 201, y_window_size = 201)
    VV = set_padding(read_image.image_array(os.getenv('VV_tif_path')), x_window_size = 201, y_window_size = 201)

    start = time.time()
    compute_covariance_matrix(HH, HV, VH, VV)
    end = time.time()