import nibabel as nib
import matplotlib.pyplot as plt
from matplotlib.widgets import RectangleSelector, Button, PolygonSelector
from matplotlib.path import Path
import numpy as np
import tkinter as tk
from tkinter import filedialog
import pyperclip


def select_nifti_file():
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    file_path = filedialog.askopenfilename(filetypes=[("NIfTI files", "*.nii;*.nii.gz")])
    return file_path


# Load NIfTI file
def load_nifti():
    img = nib.load(select_nifti_file())
    data = img.get_fdata()
    return data


# Display a slice
def display_slice(ax, slice_data):
    ax.imshow(slice_data.T, cmap="gray", origin="lower")


# Update displayed slice
def update_slice(ax, slice_data):
    ax.clear()
    display_slice(ax, slice_data)
    plt.draw()

    # Re-activate RectangleSelector on the updated axis
    global rs
    rs = PolygonSelector(ax, onselect_polygon, ops=dict(color='red', linewidth=2))


# ROI selection
global btn_copy  # Declare the button as a global variable


def onselect_polygon(vertices):
    global roi_coords
    roi_coords = vertices  # Store the polygon vertices

    # Calculate and plot the average b-values
    avg_b_values = calculate_avg_b_value_through_time(data, roi_coords)
    print(f"Average b-values within the ROI across all time points: {avg_b_values}")

    fig, ax = plt.subplots()
    plt.subplots_adjust(bottom=0.2)
    plt.plot(avg_b_values, marker='o')
    plt.title('Average b-values across Time Points')
    plt.xlabel('Time Point')
    plt.ylabel('Average b-value')

    avg_b_values_str = '\n'.join(map(str, avg_b_values))
    pyperclip.copy(avg_b_values_str)
    print("Average b-values have been copied to the clipboard.")

    plt.show()


# Calculate average b-value within ROI
def calculate_avg_b_value_through_time(data, roi_coords):
    # Create a Path object for the ROI
    roi_path = Path(roi_coords)

    # Get the dimensions of the data
    x_dim, y_dim, num_slices, num_time_points = data.shape

    # Precompute the ROI mask
    x, y = np.meshgrid(np.arange(x_dim), np.arange(y_dim))
    xy = np.column_stack((x.ravel(), y.ravel()))
    mask = roi_path.contains_points(xy).reshape(x_dim, y_dim)

    # Initialize an empty list to store the average b-values for each time point
    avg_b_values = []

    # Loop through all time points
    for t in range(num_time_points):
        # Initialize variables to keep track of the sum and count of b-values in the ROI
        sum_b_values = 0
        count = 0

        # Loop through all slices (assuming the polygon is applicable to all slices)
        for s in range(num_slices):
            slice_data = data[:, :, s, t]
            sum_b_values += np.sum(slice_data[mask])
            count += np.sum(mask)

        # Calculate the average b-value for the time point
        avg_b_value = sum_b_values / count if count > 0 else 0
        avg_b_values.append(avg_b_value)

    return avg_b_values



# Key event to scroll slices and time segments
def on_key(event):
    global current_slice, current_time, data
    if event.key == 'up':
        current_slice = min(current_slice + 1, data.shape[2] - 1)
    elif event.key == 'down':
        current_slice = max(current_slice - 1, 0)
    elif event.key == 'left':
        current_time = max(current_time - 1, 0)
    elif event.key == 'right':
        current_time = min(current_time + 1, data.shape[3] - 1 if len(data.shape) == 4 else 0)
    update_slice(ax, data[:, :, current_slice, current_time] if len(data.shape) == 4 else data[:, :, current_slice])


# Main function
if __name__ == '__main__':
    file_path = "path/to/your/nifti/file.nii"
    data = load_nifti()

    # Switch backend for interactive display
    plt.switch_backend('Tkagg')

    # Initialize slice and time segment
    current_slice = data.shape[2] // 2
    current_time = 0

    # Initialize ROI coordinates
    roi_coords = [0, 0, 0, 0]

    # Display slice
    global btn_copy
    fig, ax = plt.subplots()
    initial_slice = data[:, :, current_slice, current_time] if len(data.shape) == 4 else data[:, :, current_slice]
    display_slice(ax, initial_slice)

    # ROI selection and slice scrolling
    global rs  # Declare rs as global
    rs = PolygonSelector(ax, onselect_polygon, props=dict(color='red', linewidth=2))
    fig.canvas.mpl_connect('key_press_event', on_key)
    plt.show()

    # Calculate and display the average b-value within the ROI
    selected_slice = data[:, :, current_slice, current_time] if len(data.shape) == 4 else data[:, :, current_slice]
    avg_b_values = calculate_avg_b_value_through_time(data, roi_coords)
    print(f"Average b-values within the ROI across all time points: {avg_b_values}")
