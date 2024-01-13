import numpy as np
from PIL import Image

# Define the dimensions of the image
width = 1920
height = 1080

#6DDAFA

# Create a NumPy array with the desired color
color = np.array([109, 218, 250], dtype=np.uint8)  # RGB values for #D9D9D9

# Create an image array with the specified dimensions
image_array = np.tile(color, (height, width, 1))

# Create a PIL image from the NumPy array
image = Image.fromarray(image_array)

# Save the image as a JPEG file
image.save("d9d9d9.jpg")
