"""Test script for camera frustum opacity feature with images."""

import numpy as np
import viser

server = viser.ViserServer()

# Load real images from examples/assets
import imageio.v3 as iio
from pathlib import Path

assets_dir = Path("./examples/assets/room/images")
image_paths = [
    assets_dir / "DSCF4667.JPG",
    assets_dir / "DSCF4672.JPG",
    assets_dir / "DSCF4685.JPG",
]
images = [iio.imread(str(p)) for p in image_paths]


# Test 1: Filled frustum with image, fully opaque
img1 = images[0]
frustum1 = server.scene.add_camera_frustum(
    "/camera1_image_opaque",
    fov=np.pi / 3,
    aspect=16 / 9,
    scale=0.8,
    color=(255, 0, 0),  # Red
    opacity=1.0,  # Fully opaque
    image=img1,
    variant="wireframe",
    position=(0, 0, 0),
)

# Test 2: Filled frustum with image, medium opacity
img2 = images[1]
frustum2 = server.scene.add_camera_frustum(
    "/camera2_image_medium",
    fov=np.pi / 3,
    aspect=16 / 9,
    scale=0.8,
    color=(0, 255, 0),  # Green
    opacity=0.2,  # Medium transparency - IMAGE SHOULD BE SEMI-TRANSPARENT
    image=img2,
    variant="wireframe",
    position=(4, 0, 0),
)


print("=" * 70)
print("Camera Frustum Opacity Test - WITH IMAGES")
print("=" * 70)
print("Test server running at http://localhost:8080")
print()
print("You should see 6 camera frustums:")
print()
print("  1. RED filled with image (opacity=1.0) - FULLY OPAQUE")
print("  2. GREEN filled with image (opacity=0.6) - Image should be semi-transparent")
print("  3. BLUE filled with image (opacity=0.3) - Image should be very transparent")
print("  4. YELLOW wireframe with image (opacity=0.5) - Lines AND image semi-transparent")
print("  5. MAGENTA wireframe no image (opacity=0.4) - Only lines, semi-transparent")
print("  6. CYAN filled no image (opacity=0.5) - Faces and lines semi-transparent")
print()
print("KEY TEST: Check that images in frustums 2, 3, and 4 are transparent!")
print("=" * 70)

while True:
    pass
