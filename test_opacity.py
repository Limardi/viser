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

# Add GUI elements to the right panel (root container - default)
server.gui.add_markdown("## Right Panel Controls")
opacity_slider = server.gui.add_slider(
    "Frustum Opacity",
    min=0.0,
    max=1.0,
    initial_value=0.5,
    step=0.1,
)

# Update frustum opacity when slider changes
@opacity_slider.on_update
def _(_):
    opacity_value = opacity_slider.value
    # Update both frustums with the new opacity
    frustum1.opacity = opacity_value
    frustum2.opacity = opacity_value
    print(f"Updated frustum opacity to: {opacity_value}")

reset_button = server.gui.add_button("Reset Camera")
@reset_button.on_click
def _(_):
    print("Reset camera button clicked!")
    # You can add camera reset logic here

wireframe_checkbox = server.gui.add_checkbox("Show Wireframe", initial_value=True)
@wireframe_checkbox.on_update
def _(_):
    show_wireframe = wireframe_checkbox.value
    print(f"Show wireframe: {show_wireframe}")
    # You can add logic to toggle wireframe display here

# Add GUI elements to the left panel
# Use 'with server.gui.container("left_panel"):' to add elements to the left panel
with server.gui.container("left_panel"):
    server.gui.add_markdown("## Left Panel Controls")
    
    scale_slider = server.gui.add_slider(
        "Camera Scale",
        min=0.1,
        max=2.0,
        initial_value=0.8,
        step=0.1,
    )
    
    # Update frustum scale when slider changes
    @scale_slider.on_update
    def _(_):
        scale_value = scale_slider.value
        # Update both frustums with the new scale
        frustum1.scale = scale_value
        frustum2.scale = scale_value
        print(f"Updated frustum scale to: {scale_value}")
    
    export_button = server.gui.add_button("Export View")
    @export_button.on_click
    def _(_):
        print("Export view button clicked!")
        # You can add export logic here
    
    notes_text = server.gui.add_text("Notes", initial_value="Test opacity feature")
    @notes_text.on_update
    def _(_):
        notes_value = notes_text.value
        print(f"Notes updated: {notes_value}")
    
    # You can add more elements here - they'll all go to the left panel
    server.gui.add_markdown("---")
    server.gui.add_slider("Brightness", min=0.0, max=1.0, initial_value=0.5, step=0.1)
    server.gui.add_dropdown("Color Mode", options=["RGB", "HSV", "LAB"], initial_value="RGB")
    server.gui.add_rgb("Background Color", initial_value=(128, 128, 128))

while True:
    pass
