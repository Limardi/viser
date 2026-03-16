"""Test script for camera frustum opacity feature with images."""

import numpy as np
import viser

server = viser.ViserServer()

# Load real images from examples/assets
import imageio.v3 as iio
from pathlib import Path

assets_dir = Path("./examples/assets/0722_luffy3_jpg/images/")
image_paths = [
    assets_dir / "IMG_0001.jpg",
    assets_dir / "IMG_0002.jpg",
    assets_dir / "IMG_0003.jpg",
]
images = [iio.imread(str(p)) for p in image_paths]


# Test 1: Frustum with flat 2D lines - using separate frame and ray colors AND opacities
img1 = images[0]
frustum1 = server.scene.add_camera_frustum(
    "/camera1_flat_lines",
    fov=np.pi / 3,
    aspect=1 / 1.5,
    scale=0.8,
    color=(255, 255, 255),  # Base color (for up indicator)
    frame_color=(255, 0, 0),  # RED frame rectangle
    ray_color=(0, 0, 255),  # BLUE rays/cone
    frame_opacity=1.0,  # Frame opacity - fully opaque
    ray_opacity=0.5,  # Ray opacity - semi-transparent
    opacity=1.0,  # Image opacity - fully opaque
    line_style="flat",  # 2D flat lines
    image=img1,
    variant="wireframe",
    position=(0, 0, 0),
)

# # Test 2: Frustum with 3D tube lines - different frame and ray colors AND opacities
# img2 = images[1]
# frustum2 = server.scene.add_camera_frustum(
#     "/camera2_tube_lines",
#     fov=np.pi / 3,
#     aspect=16 / 9,
#     scale=0.8,
#     color=(255, 255, 255),  # Base color
#     frame_color=(0, 255, 0),  # GREEN frame rectangle
#     ray_color=(255, 165, 0),  # ORANGE rays/cone
#     frame_opacity=0.7,  # Frame opacity - semi-transparent
#     ray_opacity=1.0,  # Ray opacity - fully opaque
#     opacity=0.8,  # Image opacity - slightly transparent
#     line_style="tube",  # 3D tube/pipe lines
#     line_radius=0.02,  # Radius of the tubes
#     image=img2,
#     variant="wireframe",
#     position=(4, 0, 0),
# )

# # Test 3: Frustum without separate colors (backward compatibility)
# img3 = images[2]
# frustum3 = server.scene.add_camera_frustum(
#     "/camera3_single_color",
#     fov=np.pi / 3,
#     aspect=16 / 9,
#     scale=0.8,
#     color=(255, 0, 255),  # Magenta - all lines same color
#     opacity=1.0,
#     line_opacity=1.0,
#     line_style="tube",
#     line_radius=0.015,
#     image=img3,
#     variant="wireframe",
#     position=(8, 0, 0),
# )


# Test 4: Clickable line segments (simple yellow square on the ground)
edge_points = np.array(
    [
        [[-1.0, -1.0, 0.0], [1.0, -1.0, 0.0]],
        [[1.0, -1.0, 0.0], [1.0, 1.0, 0.0]],
        [[1.0, 1.0, 0.0], [-1.0, 1.0, 0.0]],
        [[-1.0, 1.0, 0.0], [-1.0, -1.0, 0.0]],
    ],
    dtype=np.float32,
)

edge_colors = np.full((4, 2, 3), fill_value=[255, 255, 0], dtype=np.uint8)  # yellow

clickable_edges = server.scene.add_line_segments(
    "/clickable_edges",
    points=edge_points,
    colors=edge_colors,
    line_width=4.0,
)


@clickable_edges.on_click
def _on_edges_click(event: viser.SceneNodePointerEvent[viser.LineSegmentsHandle]) -> None:  # type: ignore[name-defined]
    print(
        "[clickable_edges] Click detected:",
        f"screen_pos={event.screen_pos}",
        f"ray_origin={event.ray_origin}",
    )


# Test 5: Image with RED outline frame
# img_with_outline = server.scene.add_image(
#     "/image_with_outline",
#     image=images[0],
#     render_width=1.5,
#     render_height=1.0,
#     show_outline=True,
#     image_frame_color=(255, 0, 0),  # RED frame
#     image_frame_width=4.0,          # Thick lines
#     position=(0, 3, 0),
#     wxyz=(1.0, 0.0, 0.0, 0.0),
# )

# # Test 6: Image with thin GREEN outline frame
# img_green_outline = server.scene.add_image(
#     "/image_green_outline",
#     image=images[1],
#     render_width=1.5,
#     render_height=1.0,
#     show_outline=True,
#     image_frame_color=(0, 255, 0),  # GREEN frame
#     image_frame_width=1.5,          # Thin lines
#     position=(2, 3, 0),
#     wxyz=(1.0, 0.0, 0.0, 0.0),
# )

# # Test 7: Image with default yellow outline (no color specified)
# img_default_outline = server.scene.add_image(
#     "/image_default_outline",
#     image=images[2],
#     render_width=1.5,
#     render_height=1.0,
#     show_outline=True,  # Default yellow, default width
#     position=(4, 3, 0),
#     wxyz=(1.0, 0.0, 0.0, 0.0),
# )

# Side-by-side comparison: wireframe vs image_only (same image, same params)
shared_fov = np.pi / 3
shared_aspect = 16 / 9
shared_scale = 0.8
shared_color = (255, 0, 0)
shared_image = images[0]

# Left: wireframe variant (full frustum)
frustum_wireframe = server.scene.add_camera_frustum(
    "/compare_wireframe",
    fov=shared_fov,
    aspect=shared_aspect,
    scale=shared_scale,
    color=shared_color,
    image=shared_image,
    variant="wireframe",
    position=(0, 3, 0),
)

# Right: image_only variant with show_frame + show_axes
frustum_image_only = server.scene.add_camera_frustum(
    "/compare_image_only",
    fov=shared_fov,
    aspect=shared_aspect,
    scale=shared_scale,
    color=shared_color,
    frame_color=shared_color,
    image=shared_image,
    variant="image_only",
    show_frame=True,
    show_axes=True,
    position=(3, 3, 0),
)


print("=" * 70)
print("Camera Frustum Test - SEPARATE FRAME & RAY COLORS + OPACITIES")
print("=" * 70)
print("Test server running at http://localhost:8080")
print()
print("You should see 3 camera frustums:")
print()
print("  1. MULTI-COLOR frustum (LEFT):")
print("     - Frame: RED rectangle (opacity: 1.0)")
print("     - Rays: BLUE cone lines (opacity: 0.5 - semi-transparent!)")
print("     - Line style: FLAT (2D screen-space lines)")
print()
print("  2. MULTI-COLOR frustum (CENTER):")
print("     - Frame: GREEN rectangle (opacity: 0.7 - semi-transparent!)")
print("     - Rays: ORANGE cone lines (opacity: 1.0)")
print("     - Line style: TUBE (3D cylindrical pipes)")
print("     - Line radius: 0.02")
print("     - Image opacity: 0.8")
print()
print("  3. SINGLE-COLOR frustum (RIGHT):")
print("     - All lines: MAGENTA (backward compatibility)")
print("     - Line style: TUBE")
print()
print("  4. Clickable yellow square on the ground")
print()
print("  5. Image with RED outline (thick, above left)")
print("  6. Image with GREEN outline (thin, above center)")
print("  7. Image with default YELLOW outline (above right)")
print("  8. Camera frustum 'image_only' + show_frame=True + show_axes=True")
print("  9. Camera frustum 'image_only' + show_frame=True + show_axes=False (frame only)")
print("  10. Camera frustum 'image_only' + show_frame=False + show_axes=True (axes only)")
print()
print("KEY TEST: Each frustum part (frame/rays) should have")
print("          DIFFERENT colors AND opacities!")
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
    # Update image opacity for all frustums
    frustum1.opacity = opacity_value
    frustum2.opacity = opacity_value
    frustum3.opacity = opacity_value
    print(f"Updated image opacity to: {opacity_value:.2f}")

server.gui.add_markdown("### Line Opacity (affects line segments only)")
line_opacity_slider = server.gui.add_slider(
    "Line Opacity",
    min=0.0,
    max=1.0,
    initial_value=1.0,  # Match initial line opacity
    step=0.01,
)

@line_opacity_slider.on_update
def _(_):
    line_opacity_value = line_opacity_slider.value
    # Update line opacity for all frustums
    # The line_opacity property is automatically available via AssignablePropsBase
    frustum1.line_opacity = line_opacity_value
    frustum2.line_opacity = line_opacity_value
    frustum3.line_opacity = line_opacity_value
    print(f"Updated line opacity to: {line_opacity_value:.2f}")

server.gui.add_markdown("### Line Radius (for tube style)")
line_radius_slider = server.gui.add_slider(
    "Tube Line Radius",
    min=0.005,
    max=0.05,
    initial_value=0.02,
    step=0.005,
)

@line_radius_slider.on_update
def _(_):
    radius_value = line_radius_slider.value
    # Update line radius for all frustums
    frustum1.line_radius = radius_value
    frustum2.line_radius = radius_value
    frustum3.line_radius = radius_value
    print(f"Updated line radius to: {radius_value:.3f}")

server.gui.add_markdown("### Line Style")
style_toggle = server.gui.add_button("Toggle Line Style (Flat/Tube)")

@style_toggle.on_click
def _(_):
    # Toggle between flat and tube
    current_style = frustum1.line_style
    new_style = "tube" if current_style == "flat" else "flat"
    frustum1.line_style = new_style
    frustum2.line_style = new_style
    frustum3.line_style = new_style
    print(f"Switched to {new_style} line style")

server.gui.add_markdown("### Frame Color (Rectangle)")
frame_color_picker = server.gui.add_rgb(
    "Frame Color",
    initial_value=(255, 0, 0),  # Initial red
)

@frame_color_picker.on_update
def _(_):
    frame_color_value = frame_color_picker.value
    frustum1.frame_color = frame_color_value
    frustum2.frame_color = frame_color_value
    print(f"Updated frame color to: {frame_color_value}")

server.gui.add_markdown("### Ray Color (Cone Lines)")
ray_color_picker = server.gui.add_rgb(
    "Ray Color",
    initial_value=(0, 0, 255),  # Initial blue
)

@ray_color_picker.on_update
def _(_):
    ray_color_value = ray_color_picker.value
    frustum1.ray_color = ray_color_value
    frustum2.ray_color = ray_color_value
    print(f"Updated ray color to: {ray_color_value}")

server.gui.add_markdown("### Frame Opacity")
frame_opacity_slider = server.gui.add_slider(
    "Frame Opacity",
    min=0.0,
    max=1.0,
    initial_value=1.0,
    step=0.01,
)

@frame_opacity_slider.on_update
def _(_):
    frame_opacity_value = frame_opacity_slider.value
    frustum1.frame_opacity = frame_opacity_value
    frustum2.frame_opacity = frame_opacity_value
    print(f"Updated frame opacity to: {frame_opacity_value:.2f}")

server.gui.add_markdown("### Ray Opacity")
ray_opacity_slider = server.gui.add_slider(
    "Ray Opacity",
    min=0.0,
    max=1.0,
    initial_value=0.5,
    step=0.01,
)

@ray_opacity_slider.on_update
def _(_):
    ray_opacity_value = ray_opacity_slider.value
    frustum1.ray_opacity = ray_opacity_value
    frustum2.ray_opacity = ray_opacity_value
    print(f"Updated ray opacity to: {ray_opacity_value:.2f}")

server.gui.add_markdown("### Side-by-Side Controls")

show_frame_checkbox = server.gui.add_checkbox("Show Frame Border", initial_value=True)
@show_frame_checkbox.on_update
def _(_):
    val = show_frame_checkbox.value
    frustum_image_only.show_frame = val
    print(f"show_frame = {val}")

show_axes_checkbox = server.gui.add_checkbox("Show Up Indicator", initial_value=True)
@show_axes_checkbox.on_update
def _(_):
    val = show_axes_checkbox.value
    frustum_image_only.show_axes = val
    print(f"show_axes = {val}")

frame_color_io = server.gui.add_rgb("Border Color", initial_value=(255, 0, 0))
@frame_color_io.on_update
def _(_):
    val = frame_color_io.value
    frustum_image_only.frame_color = val
    frustum_wireframe.frame_color = val
    print(f"frame_color = {val}")

io_line_width = server.gui.add_slider("Line Width", min=0.5, max=8.0, initial_value=2.0, step=0.5)
@io_line_width.on_update
def _(_):
    val = io_line_width.value
    frustum_image_only.line_width = val
    frustum_wireframe.line_width = val
    print(f"line_width = {val}")

io_scale = server.gui.add_slider("Scale", min=0.1, max=3.0, initial_value=0.8, step=0.1)
@io_scale.on_update
def _(_):
    val = io_scale.value
    frustum_image_only.scale = val
    frustum_wireframe.scale = val
    print(f"scale = {val}")

io_opacity = server.gui.add_slider("Image Opacity", min=0.0, max=1.0, initial_value=1.0, step=0.01)
@io_opacity.on_update
def _(_):
    val = io_opacity.value
    frustum_image_only.opacity = val
    frustum_wireframe.opacity = val
    print(f"image opacity = {val:.2f}")

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
        # Update all frustums with the new scale
        frustum1.scale = scale_value
        frustum2.scale = scale_value
        frustum3.scale = scale_value
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
