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


# Test 1: Filled frustum with image, separate line and image opacity
img1 = images[0]
frustum1 = server.scene.add_camera_frustum(
    "/camera1_image_opaque",
    fov=np.pi / 3,
    aspect=16 / 9,
    scale=0.8,
    color=(255, 0, 0),  # Red
    opacity=1.0,  # Image opacity - fully opaque
    line_opacity=0.5,  # Line opacity - semi-transparent lines
    image=img1,
    variant="wireframe",
    position=(0, 0, 0),
)

# Test 2: Filled frustum with image, different opacities
img2 = images[1]
frustum2 = server.scene.add_camera_frustum(
    "/camera2_image_medium",
    fov=np.pi / 3,
    aspect=16 / 9,
    scale=0.8,
    color=(0, 255, 0),  # Green
    opacity=0.3,  # Image opacity - very transparent image
    line_opacity=1.0,  # Line opacity - fully opaque lines
    image=img2,
    variant="wireframe",
    position=(4, 0, 0),
)


print("=" * 70)
print("Camera Frustum Opacity Test - SEPARATE LINE AND IMAGE OPACITY")
print("=" * 70)
print("Test server running at http://localhost:8080")
print()
print("You should see 2 camera frustums:")
print()
print("  1. RED frustum:")
print("     - Image opacity: 1.0 (fully opaque)")
print("     - Line opacity: 0.5 (semi-transparent lines)")
print()
print("  2. GREEN frustum:")
print("     - Image opacity: 0.3 (very transparent image)")
print("     - Line opacity: 1.0 (fully opaque lines)")
print()
print("KEY TEST: Lines and images should have independent opacity!")
print("=" * 70)

# Add GUI elements to the right panel (root container - default)
server.gui.add_markdown("## Right Panel Controls")

# Separate controls for line opacity and image opacity
server.gui.add_markdown("### Image Opacity (affects image and filled faces)")
image_opacity_slider = server.gui.add_slider(
    "Image Opacity",
    min=0.0,
    max=1.0,
    initial_value=1.0,  # Match frustum1's initial image opacity
    step=0.01,
)

@image_opacity_slider.on_update
def _(_):
    opacity_value = image_opacity_slider.value
    # Update image opacity for both frustums
    frustum1.opacity = opacity_value
    frustum2.opacity = opacity_value
    print(f"Updated image opacity to: {opacity_value:.2f}")

server.gui.add_markdown("### Line Opacity (affects line segments only)")
line_opacity_slider = server.gui.add_slider(
    "Line Opacity",
    min=0.0,
    max=1.0,
    initial_value=0.5,  # Match frustum1's initial line opacity
    step=0.01,
)

@line_opacity_slider.on_update
def _(_):
    line_opacity_value = line_opacity_slider.value
    # Update line opacity for both frustums
    # The line_opacity property is automatically available via AssignablePropsBase
    frustum1.line_opacity = line_opacity_value
    frustum2.line_opacity = line_opacity_value
    print(f"Updated line opacity to: {line_opacity_value:.2f}")

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
