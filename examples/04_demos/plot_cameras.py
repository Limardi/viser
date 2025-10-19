"""Simple camera position visualization using matplotlib."""

from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

import viser.transforms as vtf
from viser.extras.colmap import read_cameras_binary, read_images_binary


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


def main():
    # Path to COLMAP data
    colmap_path = Path(__file__).parent / "../assets/0722_luffy3_jpg/sparse/0"
    
    # Load the colmap info
    cameras = read_cameras_binary(colmap_path / "cameras.bin")
    images = read_images_binary(colmap_path / "images.bin")
    
    # Extract camera positions and orientations
    cam_positions = []
    cam_up_vectors = []  # "up" direction for each camera
    cam_forward_vectors = []  # "forward" direction for each camera
    
    cam_local_up = np.array([0.0, -1.0, 0.0])
    cam_local_forward = np.array([0.0, 0.0, 1.0])
    
    for img in images.values():
        # Get camera-to-world transformation
        T_world_camera = vtf.SE3.from_rotation_and_translation(
            vtf.SO3(img.qvec), img.tvec
        ).inverse()
        
        # Camera position in world coordinates
        position = T_world_camera.translation()
        cam_positions.append(position)
        
        # Transform camera's local "up" to world coordinates
        R_cam_to_world = vtf.SO3(img.qvec).inverse()
        world_up = R_cam_to_world @ cam_local_up
        world_forward = R_cam_to_world @ cam_local_forward
        
        cam_up_vectors.append(world_up)
        cam_forward_vectors.append(world_forward)
    
    cam_positions = np.array(cam_positions)
    cam_up_vectors = np.array(cam_up_vectors)
    cam_forward_vectors = np.array(cam_forward_vectors)
    
    # Compute average up direction
    average_up = cam_up_vectors.mean(axis=0)
    average_up /= np.linalg.norm(average_up)
    
    # Compute scene center
    scene_center = cam_positions.mean(axis=0)
    
    # ====== APPLY REORIENTATION (like in the original code) ======
    target_up = np.array([0.0, 0.0, 1.0])  # we want +Z up in viewer
    R_align = rot_from_a_to_b(average_up, target_up)  # 3x3 rotation matrix
    
    # Apply rotation to reorient the scene
    # Rotate positions around scene center
    cam_positions_reoriented = (R_align @ (cam_positions - scene_center).T).T
    # Rotate up vectors
    cam_up_vectors_reoriented = (R_align @ cam_up_vectors.T).T
    # Compute new average up (should be ~[0, 0, 1])
    average_up_reoriented = (R_align @ average_up)
    
    # ====== CREATE BEFORE/AFTER VISUALIZATION ======
    fig = plt.figure(figsize=(18, 10))
    
    # ===== TOP ROW: BEFORE REORIENTATION =====
    
    # Plot 1: Original camera positions with up vectors
    ax1 = fig.add_subplot(231, projection='3d')
    ax1.scatter(cam_positions[:, 0], cam_positions[:, 1], cam_positions[:, 2], 
                c='blue', marker='o', s=20, alpha=0.6, label='Cameras')
    
    # Plot up vectors (sample to avoid clutter)
    step = max(1, len(cam_positions) // 15)
    for i in range(0, len(cam_positions), step):
        pos = cam_positions[i]
        up = cam_up_vectors[i] * 0.5
        ax1.quiver(pos[0], pos[1], pos[2], 
                   up[0], up[1], up[2], 
                   color='red', alpha=0.5, arrow_length_ratio=0.3)
    
    ax1.set_xlabel('X')
    ax1.set_ylabel('Y')
    ax1.set_zlabel('Z')
    ax1.set_title('BEFORE: Original COLMAP Coordinates\n(with camera up vectors in red)')
    ax1.grid(True)
    
    # Plot 2: Original with average up vector
    ax2 = fig.add_subplot(232, projection='3d')
    ax2.scatter(cam_positions[:, 0], cam_positions[:, 1], cam_positions[:, 2], 
                c='blue', marker='o', s=20, alpha=0.6)
    
    # Plot average up vector from scene center
    avg_up_scaled = average_up * 2.0
    ax2.quiver(scene_center[0], scene_center[1], scene_center[2],
               avg_up_scaled[0], avg_up_scaled[1], avg_up_scaled[2],
               color='green', linewidth=4, arrow_length_ratio=0.2, label='Avg Up')
    
    # Also plot target Z axis for comparison
    target_scaled = target_up * 2.0
    ax2.quiver(scene_center[0], scene_center[1], scene_center[2],
               target_scaled[0], target_scaled[1], target_scaled[2],
               color='orange', linewidth=3, arrow_length_ratio=0.2, linestyle='--', 
               label='Target +Z')
    
    ax2.set_xlabel('X')
    ax2.set_ylabel('Y')
    ax2.set_zlabel('Z')
    ax2.set_title(f'BEFORE: Average Up (green)\nvs Target +Z (orange)\navg_up={average_up}')
    ax2.legend()
    ax2.grid(True)
    
    # Plot 3: Original - view from different angle
    ax3 = fig.add_subplot(233, projection='3d')
    ax3.scatter(cam_positions[:, 0], cam_positions[:, 1], cam_positions[:, 2], 
                c='blue', marker='o', s=20, alpha=0.6)
    ax3.quiver(scene_center[0], scene_center[1], scene_center[2],
               avg_up_scaled[0], avg_up_scaled[1], avg_up_scaled[2],
               color='green', linewidth=4, arrow_length_ratio=0.2)
    ax3.set_xlabel('X')
    ax3.set_ylabel('Y')
    ax3.set_zlabel('Z')
    ax3.set_title('BEFORE: Side View')
    ax3.view_init(elev=0, azim=0)  # Side view
    ax3.grid(True)
    
    # ===== BOTTOM ROW: AFTER REORIENTATION =====
    
    # Plot 4: Reoriented camera positions with up vectors
    ax4 = fig.add_subplot(234, projection='3d')
    ax4.scatter(cam_positions_reoriented[:, 0], cam_positions_reoriented[:, 1], 
                cam_positions_reoriented[:, 2], c='blue', marker='o', s=20, alpha=0.6)
    
    # Plot reoriented up vectors
    for i in range(0, len(cam_positions_reoriented), step):
        pos = cam_positions_reoriented[i]
        up = cam_up_vectors_reoriented[i] * 0.5
        ax4.quiver(pos[0], pos[1], pos[2], 
                   up[0], up[1], up[2], 
                   color='red', alpha=0.5, arrow_length_ratio=0.3)
    
    ax4.set_xlabel('X')
    ax4.set_ylabel('Y')
    ax4.set_zlabel('Z')
    ax4.set_title('AFTER: Reoriented Coordinates\n(camera up vectors now point toward +Z)')
    ax4.grid(True)
    
    # Plot 5: Reoriented with average up
    ax5 = fig.add_subplot(235, projection='3d')
    ax5.scatter(cam_positions_reoriented[:, 0], cam_positions_reoriented[:, 1], 
                cam_positions_reoriented[:, 2], c='blue', marker='o', s=20, alpha=0.6)
    
    # Plot reoriented average up (should align with +Z)
    avg_up_reoriented_scaled = average_up_reoriented * 2.0
    ax5.quiver(0, 0, 0,  # Scene center is now at origin
               avg_up_reoriented_scaled[0], avg_up_reoriented_scaled[1], 
               avg_up_reoriented_scaled[2],
               color='green', linewidth=4, arrow_length_ratio=0.2, label='Avg Up (aligned)')
    
    ax5.quiver(0, 0, 0,
               target_scaled[0], target_scaled[1], target_scaled[2],
               color='orange', linewidth=3, arrow_length_ratio=0.2, linestyle='--',
               label='Target +Z')
    
    ax5.set_xlabel('X')
    ax5.set_ylabel('Y')
    ax5.set_zlabel('Z')
    ax5.set_title(f'AFTER: Average Up (green) aligned with +Z\navg_up={average_up_reoriented}')
    ax5.legend()
    ax5.grid(True)
    
    # Plot 6: Reoriented - side view
    ax6 = fig.add_subplot(236, projection='3d')
    ax6.scatter(cam_positions_reoriented[:, 0], cam_positions_reoriented[:, 1], 
                cam_positions_reoriented[:, 2], c='blue', marker='o', s=20, alpha=0.6)
    ax6.quiver(0, 0, 0,
               avg_up_reoriented_scaled[0], avg_up_reoriented_scaled[1], 
               avg_up_reoriented_scaled[2],
               color='green', linewidth=4, arrow_length_ratio=0.2)
    ax6.set_xlabel('X')
    ax6.set_ylabel('Y')
    ax6.set_zlabel('Z')
    ax6.set_title('AFTER: Side View\n(+Z is now "up")')
    ax6.view_init(elev=0, azim=0)  # Side view
    ax6.grid(True)
    
    plt.tight_layout()
    
    # Print some statistics
    print("="*60)
    print("BEFORE REORIENTATION:")
    print(f"  Number of cameras: {len(cam_positions)}")
    print(f"  Scene center: {scene_center}")
    print(f"  Average up direction: {average_up}")
    print(f"  Camera position range:")
    print(f"    X: [{cam_positions[:, 0].min():.2f}, {cam_positions[:, 0].max():.2f}]")
    print(f"    Y: [{cam_positions[:, 1].min():.2f}, {cam_positions[:, 1].max():.2f}]")
    print(f"    Z: [{cam_positions[:, 2].min():.2f}, {cam_positions[:, 2].max():.2f}]")
    
    print("\n" + "="*60)
    print("AFTER REORIENTATION:")
    print(f"  Average up direction: {average_up_reoriented}")
    print(f"  Dot product with target +Z: {np.dot(average_up_reoriented, target_up):.6f}")
    print(f"  (Should be ~1.0, meaning they're aligned)")
    print(f"  Camera position range:")
    print(f"    X: [{cam_positions_reoriented[:, 0].min():.2f}, {cam_positions_reoriented[:, 0].max():.2f}]")
    print(f"    Y: [{cam_positions_reoriented[:, 1].min():.2f}, {cam_positions_reoriented[:, 1].max():.2f}]")
    print(f"    Z: [{cam_positions_reoriented[:, 2].min():.2f}, {cam_positions_reoriented[:, 2].max():.2f}]")
    print("="*60)
    
    plt.show()


if __name__ == "__main__":
    main()

