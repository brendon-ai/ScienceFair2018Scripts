#!/usr/bin/env python3

import os
import random
import sys
import uuid

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtWidgets import QLabel, QWidget, QApplication
from skimage.io import imread, imsave

# Program which allows a user to select the position of an object in a wide image
# in order to create training data for a convolutional neural network
# Created by brendon-ai, September 2017


# Width of the window
WINDOW_WIDTH = 1920

# Height of output training images (width is the same as that of the input images)
OUTPUT_HEIGHT = 16


# Main PyQt5 QWidget class
class ManualSelection(QWidget):
    # Height of the window, calculated when the UI is set up
    window_height = None

    # The label that displays the current image
    image_box = None

    # The current image as a NumPy array
    current_image = None

    # The index of the next image's path in the paths list
    current_image_index = 0

    # List of fully qualified file paths of images
    image_paths = None

    # Factor by which images are scaled up to be displayed (computed at runtime)
    image_scaling_factor = None

    # A list of two-dimensional points that the user places on the image
    # Used as positive training examples
    selected_points = []

    # Call various initialization functions
    def __init__(self):

        # Call the QWidget initializer
        super(ManualSelection, self).__init__()

        # Check that the number of command line arguments is correct
        if len(sys.argv) != 3:
            print('Usage:', sys.argv[0], '<input image folder> <output image folder>')
            sys.exit()

        # Load the images from the path supplied as a command line argument
        image_folder = os.path.expanduser(sys.argv[1])
        self.image_paths = get_image_paths(image_folder)

        # Get the height and width of the first image in order to calculate the aspect ratio
        image_height, image_width = imread(self.image_paths[0]).shape[:2]

        # Calculate the scale of the window compared to the image
        # This must be an integer
        self.image_scaling_factor = WINDOW_WIDTH // image_width

        # Multiply the image height by the scale to get the window height
        self.window_height = image_height * self.image_scaling_factor

        # Set up the UI using the predefined width and computed height of the window
        self.init_ui()

    # Initialize the user interface
    def init_ui(self):

        # Set the size, title, and color scheme of the window
        self.setFixedSize(WINDOW_WIDTH, self.window_height)
        self.setWindowTitle('Manual Training Data Selection')

        # Initialize the image box that holds the video frames
        self.image_box = QLabel(self)
        self.image_box.setAlignment(Qt.AlignCenter)
        self.image_box.setFixedSize(WINDOW_WIDTH, self.window_height)
        self.image_box.move(0, 0)

        # Make the window exist
        self.show()

        # Display the initial image
        self.update_current_image()

    # Listen for mouse clicks and record their positions
    def mousePressEvent(self, mouse_event):

        # Record the current mouse position to the window path list as a two-element tuple
        # Divide it by a scaling factor so that positions apply to the original unscaled image
        mouse_position = (
            mouse_event.x() // self.image_scaling_factor,
            mouse_event.y() // self.image_scaling_factor
        )
        self.selected_points.append(mouse_position)

    # Listen for key presses and update the image when the space bar is pressed
    def keyPressEvent(self, key_event):

        # Check if the space bar was pressed
        if key_event.key() == Qt.Key_Space:

            # Save the current image data and clear the line path
            output_folder = os.path.expanduser(sys.argv[2])
            save_training_data(self.current_image, self.selected_points, output_folder)
            self.selected_points = []

            # If there are no images left that we haven't read, exit the application
            if self.current_image_index == len(self.image_paths):
                sys.exit()
            else:
                # If there are images left, update the current image
                self.update_current_image()

    # Update the current image, including the display box
    def update_current_image(self):

        # Get the path corresponding to the current index and load the image from disk
        current_path = self.image_paths[self.current_image_index]
        self.current_image = imread(current_path)

        # Convert the NumPy array into a QImage for display
        height, width, channel = self.current_image.shape
        bytes_per_line = channel * width
        current_image_qimage = QImage(self.current_image.data, width, height, bytes_per_line, QImage.Format_RGB888)
        current_image_qpixmap = QPixmap(current_image_qimage).scaled(WINDOW_WIDTH, self.window_height)

        # Fill the image box with the picture
        self.image_box.setPixmap(current_image_qpixmap)

        # Update the index of the current image
        self.current_image_index += 1


# Load paths of all of the files contained in a specific folder
def get_image_paths(folder):
    # List to store file paths of images in
    image_paths = []

    # Append the folder path to the image name for every image
    for name in os.listdir(folder):
        path = folder + '/' + name
        image_paths.append(path)

    # Randomize the order of the images
    random.shuffle(image_paths)

    return image_paths


# Slice and save data derived from a single image
def save_training_data(image, selected_points, output_folder):
    # For every defined point, we take a slice of the image centered on the point's vertical value
    for selected_point in selected_points:

        # Calculate the top and bottom limits of the slice
        vertical_slice_start = selected_point[1] - (OUTPUT_HEIGHT // 2)
        vertical_slice_end = vertical_slice_start + OUTPUT_HEIGHT

        # Slice the image's NumPy array representation
        image_slice = image[vertical_slice_start:vertical_slice_end, :, :]

        # Only save the image if the height of the slice is as expected and it is not clipped by the edge of the image
        if image_slice.shape[0] == OUTPUT_HEIGHT:
            # Use the Unix time and the position of the current road line point in the file name
            file_name = '{}/x{}_y{}_{}.png'.format(output_folder, selected_point[0], selected_point[1], uuid.uuid4())

            # Save the image
            imsave(file_name, image_slice)


# If this file is being run directly, instantiate the ManualSelection class
if __name__ == '__main__':
    app = QApplication([])
    ic = ManualSelection()
    sys.exit(app.exec_())
