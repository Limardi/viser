"""COLMAP

Visualize COLMAP sparse reconstruction outputs. To get demo data, see `../assets/download_assets.sh`.

**Features:**

* COLMAP sparse reconstruction file parsing
* Camera frustum visualization with :meth:`viser.SceneApi.add_camera_frustum`
* 3D point cloud display from structure-from-motion
* Interactive camera and point visibility controls

.. note::
    This example requires external assets. To download them, run:

    .. code-block:: bash

        git clone https://github.com/nerfstudio-project/viser.git
        cd viser/examples
        ./assets/download_assets.sh
        python 04_demos/01_colmap_visualizer.py  # With viser installed.
"""

import random
import time
from pathlib import Path
from typing import List

import imageio.v3 as iio
import numpy as np
import tyro
from tqdm.auto import tqdm

import viser
import viser.transforms as vtf
from viser.extras.colmap import (
    read_cameras_binary,
    read_images_binary,
    read_points3d_binary,
)
a
def rot_from_a_to_b(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Return a 3x3 rotation matrix that rotates unit vector a onto unit vector b."""
    a = a / np.linalg.norm(a); b = b / np.linalg.norm(b)
    v = np.cross(a, b)
    c = float(np.dot(a, b))
    if np.isclose(c, 1.0):      # already aligned
        return np.eye(3)
    if np.isclose(c, -1.0):     # opposite: pick any orthogonal axis
        # find a vector orthogonal to a
        tmp = np.array([1.0, 0.0, 0.0]) if abs(a[0]) < 0.9 else np.array([0.0, 1.0, 0.0])
        axis = np.cross(a, tmp); axis /= np.linalg.norm(axis)
        # Rodrigues with theta=pi
        K = np.array([[0, -axis[2], axis[1]],
                      [axis[2], 0, -axis[0]],
                      [-axis[1], axis[0], 0]])
        return -np.eye(3) + 2*np.outer(axis, axis)
    # general case (Rodrigues)
    s = np.linalg.norm(v)
    K = np.array([[0, -v[2], v[1]],
                  [v[2], 0, -v[0]],
                  [-v[1], v[0], 0]])
    return np.eye(3) + K + K @ K * ((1 - c) / (s**2))


def main(
    colmap_path: Path = Path(__file__).parent / "../assets/room/sparse/0",
    images_path: Path = Path(__file__).parent / "../assets/room/images",
    downsample_factor: int = 2,
    reorient_scene: bool = True,
) -> None:
    """Visualize COLMAP sparse reconstruction outputs.

    Args:
        colmap_path: Path to the COLMAP reconstruction directory.
        images_path: Path to the COLMAP images directory.
        downsample_factor: Downsample factor for the images.
    """
    server = viser.ViserServer()
    server.gui.configure_theme(titlebar_content=None, control_layout="collapsible")

    server.scene.set_up_direction((0.0, 0.0, 1.0))  # +Z is up
    # Load the colmap info.
    cameras = read_cameras_binary(colmap_path / "cameras.bin")
    images = read_images_binary(colmap_path / "images.bin")
    points3d = read_points3d_binary(colmap_path / "points3D.bin")

    points = np.array([points3d[p_id].xyz for p_id in points3d])
    colors = np.array([points3d[p_id].rgb for p_id in points3d])

    gui_reset_up = server.gui.add_button(
        "Reset up direction",
        hint="Set the camera control 'up' direction to the current camera's 'up'.",
    )

    # Let's rotate the scene so the average camera direction is pointing up.
    if reorient_scene:
        cam_local_up = np.array([0.0, -1.0, 0.0])
        world_up_samples = np.array([
            (vtf.SO3(img.qvec).inverse() @ cam_local_up)  # qvec is world->cam; invert to cam->world
            for img in images.values()
        ])
        average_up = world_up_samples.mean(axis=0)
        average_up /= np.linalg.norm(average_up)

        target_up = np.array([0.0, 0.0, 1.0])  # we want +Z up in viewer
        R_align = rot_from_a_to_b(average_up, target_up)  # 3x3
        Twc_all = [
            vtf.SE3.from_rotation_and_translation(vtf.SO3(img.qvec), img.tvec).inverse()
            for img in images.values()
        ]
        cam_positions = np.stack([Twc.translation() for Twc in Twc_all], axis=0)
        scene_center = cam_positions.mean(axis=0)

        # (keep pts_np for rotating points later)
        pts_np = np.array([points3d[p_id].xyz for p_id in points3d])

        def apply_RT(R: np.ndarray, t: np.ndarray) -> (np.ndarray, np.ndarray):
            # Rotate the WORLD by R_align and recenter at scene_center
            R_new = R_align @ R
            t_new = R_align @ (t - scene_center)
            return R_new, t_new

        # Precompute reoriented points/colors
        points = (R_align @ (pts_np - scene_center).T).T
        colors = np.array([points3d[p_id].rgb for p_id in points3d])

        # Tell the viewer that +Z is up for orbit controls.
        server.scene.set_up_direction((0.0, 0.0, 1.0))
    else:
        # Identity fallback so the code still runs when reorient_scene=False
        R_align = np.eye(3)
        scene_center = np.zeros(3)

        def apply_RT(R: np.ndarray, t: np.ndarray):
            return R, t
            
    @gui_reset_up.on_click
    def _(event: viser.GuiEvent) -> None:
        client = event.client
        assert client is not None
        client.camera.up_direction = vtf.SO3(client.camera.wxyz) @ np.array(
            [0.0, -1.0, 0.0]
        )

    gui_points = server.gui.add_slider(
        "Max points",
        min=1,
        max=len(points3d),
        step=1,
        initial_value=min(len(points3d), 50_000),
    )
    gui_frames = server.gui.add_slider(
        "Max frames",
        min=1,
        max=len(images),
        step=1,
        initial_value=min(len(images), 50),
    )
    gui_point_size = server.gui.add_slider(
        "Point size", min=0.01, max=0.1, step=0.001, initial_value=0.02
    )

    point_mask = np.random.choice(points.shape[0], gui_points.value, replace=False)
    point_cloud = server.scene.add_point_cloud(
        name="/colmap/pcd",
        points=points[point_mask],
        colors=colors[point_mask],
        point_size=gui_point_size.value,
    )
    frames: List[viser.FrameHandle] = []

    def visualize_frames() -> None:
        """Send all COLMAP elements to viser for visualization. This could be optimized
        a ton!"""

        # Remove existing image frames.
        for frame in frames:
            frame.remove()
        frames.clear()

        # Interpret the images and cameras.
        img_ids = [im.id for im in images.values()]
        random.shuffle(img_ids)
        img_ids = sorted(img_ids[: gui_frames.value])

        for img_id in tqdm(img_ids):
            img = images[img_id]
            cam = cameras[img.camera_id]

            # Skip images that don't exist.
            image_filename = images_path / img.name
            if not image_filename.exists():
                continue

            T_world_camera = (
                vtf.SE3.from_rotation_and_translation(vtf.SO3(img.qvec), img.tvec).inverse()
            )
            R_wc = T_world_camera.rotation().as_matrix()   # 3x3
            t_wc = T_world_camera.translation()            # (3,)

            R_wc_new, t_wc_new = apply_RT(R_wc, t_wc)

            # depending on viser version, one of these constructors exists:
            try:
                wxyz_new = vtf.SO3.from_matrix(R_wc_new).wxyz
            except AttributeError:
                wxyz_new = vtf.SO3(R_wc_new).wxyz

            frame = server.scene.add_frame(
                f"/colmap/frame_{img_id}",
                wxyz=wxyz_new,
                position=t_wc_new,
                axes_length=0.1,
                axes_radius=0.005,
            )
            frames.append(frame)

            # For pinhole cameras, cam.params will be (fx, fy, cx, cy).
            if cam.model != "PINHOLE":
                print(f"Expected pinhole camera, but got {cam.model}")

            H, W = cam.height, cam.width
            fy = cam.params[1]
            image = iio.imread(image_filename)
            image = image[::downsample_factor, ::downsample_factor]
            frustum = server.scene.add_camera_frustum(
                f"/colmap/frame_{img_id}/frustum",
                fov=2 * np.arctan2(H / 2, fy),
                aspect=W / H,
                scale=0.15,
                image=image,
            )

            @frustum.on_click
            def _(_, frame=frame) -> None:
                for client in server.get_clients().values():
                    client.camera.wxyz = frame.wxyz
                    client.camera.position = frame.position

    need_update = True

    @gui_points.on_update
    def _(_) -> None:
        point_mask = np.random.choice(points.shape[0], gui_points.value, replace=False)
        with server.atomic():
            point_cloud.points = points[point_mask]
            point_cloud.colors = colors[point_mask]

    @gui_frames.on_update
    def _(_) -> None:
        nonlocal need_update
        need_update = True

    @gui_point_size.on_update
    def _(_) -> None:
        point_cloud.point_size = gui_point_size.value

    while True:
        if need_update:
            need_update = False
            visualize_frames()

        time.sleep(1e-3)


if __name__ == "__main__":
    tyro.cli(main)
