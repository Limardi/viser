import { Line } from "@react-three/drei";
import { useFrame } from "@react-three/fiber";
import React from "react";
import { HoverableContext } from "./HoverContext";
import * as THREE from "three";
import { CameraFrustumMessage } from "./WebsocketMessages";
import { rgbToInt } from "./mesh/MeshUtils";

/** Helper component to render a 3D tube/pipe between two points */
function LineTube({
  start,
  end,
  radius,
  color,
  opacity,
}: {
  start: [number, number, number];
  end: [number, number, number];
  radius: number;
  color: THREE.Color | number;
  opacity: number;
}) {
  const geometry = React.useMemo(() => {
    const startVec = new THREE.Vector3(...start);
    const endVec = new THREE.Vector3(...end);
    const direction = new THREE.Vector3().subVectors(endVec, startVec);
    const length = direction.length();
    
    // Create cylinder geometry
    return new THREE.CylinderGeometry(radius, radius, length, 8);
  }, [start, end, radius]);

  const position = React.useMemo(() => {
    const startVec = new THREE.Vector3(...start);
    const endVec = new THREE.Vector3(...end);
    return new THREE.Vector3()
      .addVectors(startVec, endVec)
      .multiplyScalar(0.5);
  }, [start, end]);

  const rotation = React.useMemo(() => {
    const startVec = new THREE.Vector3(...start);
    const endVec = new THREE.Vector3(...end);
    const direction = new THREE.Vector3().subVectors(endVec, startVec);
    direction.normalize();
    
    // Create quaternion to rotate cylinder (default orientation is along Y axis)
    const quaternion = new THREE.Quaternion();
    quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), direction);
    
    return new THREE.Euler().setFromQuaternion(quaternion);
  }, [start, end]);

  return (
    <mesh geometry={geometry} position={position} rotation={rotation}>
      <meshBasicMaterial
        color={color}
        transparent={opacity < 1.0}
        opacity={opacity}
      />
    </mesh>
  );
}

/** Helper for visualizing camera frustums. */
export const CameraFrustumComponent = React.forwardRef<
  THREE.Group,
  CameraFrustumMessage & { children?: React.ReactNode }
>(function CameraFrustumComponent({ children, ...message }, ref) {
  // We can't use useMemo here because TextureLoader.load is asynchronous.
  // And we need to use setState to update the texture after loading.
  const [imageTexture, setImageTexture] = React.useState<THREE.Texture>();

  React.useEffect(() => {
    if (message.props._format !== null && message.props._image_data !== null) {
      const image_url = URL.createObjectURL(
        new Blob([message.props._image_data], {
          type: "image/" + message.props._format,
        }),
      );
      new THREE.TextureLoader().load(image_url, (texture) => {
        setImageTexture(texture);
        URL.revokeObjectURL(image_url);
      });
    } else {
      setImageTexture(undefined);
    }
  }, [message.props._format, message.props._image_data]);

  let y = Math.tan(message.props.fov / 2.0);
  let x = y * message.props.aspect;
  let z = 1.0;

  const volumeScale = Math.cbrt((x * y * z) / 3.0);
  x /= volumeScale;
  y /= volumeScale;
  z /= volumeScale;
  x *= message.props.scale;
  y *= message.props.scale;
  z *= message.props.scale;

  const hoverContext = React.useContext(HoverableContext);
  const [isHovered, setIsHovered] = React.useState(false);

  useFrame(() => {
    if (
      hoverContext !== null &&
      hoverContext.state.current.isHovered !== isHovered
    ) {
      setIsHovered(hoverContext.state.current.isHovered);
    }
  });

  const frustumPoints: [number, number, number][] = [
    // Rectangle.
    [-1, -1, 1],
    [1, -1, 1],
    [1, -1, 1],
    [1, 1, 1],
    [1, 1, 1],
    [-1, 1, 1],
    [-1, 1, 1],
    [-1, -1, 1],
    // Lines to origin.
    [-1, -1, 1],
    [0, 0, 0],
    [0, 0, 0],
    [1, -1, 1],
    // Lines to origin.
    [-1, 1, 1],
    [0, 0, 0],
    [0, 0, 0],
    [1, 1, 1],
    // Up direction indicator.
    // Don't overlap with the image if the image is present.
    [0.0, -1.2, 1.0],
    imageTexture === undefined ? [0.0, -0.9, 1.0] : [0.0, -1.0, 1.0],
  ].map((xyz) => [xyz[0] * x, xyz[1] * y, xyz[2] * z]);

  // Create geometry for filled variant
  const geometry = React.useMemo(() => {
    if (message.props.variant !== "filled") return null;

    const geom = new THREE.BufferGeometry();

    // Define vertices
    const vertices = new Float32Array([
      // Near plane (origin)
      0,
      0,
      0,
      // Far plane corners
      -x,
      -y,
      z,
      x,
      -y,
      z,
      x,
      y,
      z,
      -x,
      y,
      z,
    ]);

    // Define faces
    const indices = new Uint16Array([
      // Side faces
      0, 1, 2, 0, 2, 3, 0, 3, 4, 0, 4, 1,
      // Far plane
      1, 4, 3, 1, 3, 2,
    ]);

    geom.setAttribute("position", new THREE.BufferAttribute(vertices, 3));
    geom.setIndex(new THREE.BufferAttribute(indices, 1));
    geom.computeVertexNormals();

    return geom;
  }, [x, y, z, message.props.variant]);

  const color = new THREE.Color().setRGB(
    message.props.color[0] / 255,
    message.props.color[1] / 255,
    message.props.color[2] / 255,
  );

  // Separate opacities: line_opacity for lines, opacity for image and filled faces
  // Type assertion needed until auto-generated types are updated
  const props = message.props as typeof message.props & { 
    line_opacity?: number | null;
    line_style?: "flat" | "tube";
    line_radius?: number;
  };
  const lineOpacity = props.line_opacity ?? props.opacity ?? 1.0;
  const imageOpacity = props.opacity ?? 1.0;
  const lineStyle = props.line_style ?? "flat";
  const lineRadius = props.line_radius ?? 0.01;

  // Generate line segments for tube rendering
  const lineSegments = React.useMemo(() => {
    const segments: Array<[[number, number, number], [number, number, number]]> = [];
    // frustumPoints is an array of points defining line segments
    // Every two consecutive points form a line segment
    for (let i = 0; i < frustumPoints.length; i += 2) {
      if (i + 1 < frustumPoints.length) {
        segments.push([frustumPoints[i], frustumPoints[i + 1]]);
      }
    }
    return segments;
  }, [frustumPoints]);

  return (
    <group ref={ref}>
      {/* Wireframe lines - flat or tube based on line_style */}
      {lineStyle === "flat" ? (
        <Line
          points={frustumPoints}
          color={isHovered ? 0xfbff00 : rgbToInt(message.props.color)}
          lineWidth={
            isHovered ? 1.5 * message.props.line_width : message.props.line_width
          }
          segments
          opacity={lineOpacity}
          transparent={lineOpacity < 1.0}
        />
      ) : (
        <>
          {lineSegments.map((segment, idx) => (
            <LineTube
              key={idx}
              start={segment[0]}
              end={segment[1]}
              radius={lineRadius}
              color={isHovered ? 0xfbff00 : color}
              opacity={lineOpacity}
            />
          ))}
        </>
      )}

      {/* Filled faces - only for "filled" variant, use image opacity */}
      {message.props.variant === "filled" && geometry && (
        <mesh geometry={geometry}>
          <meshBasicMaterial
            color={isHovered ? 0xfbff00 : color}
            transparent={imageOpacity < 1.0}
            opacity={imageOpacity}
            side={THREE.DoubleSide}
            depthWrite={false}
          />
        </mesh>
      )}

      {/* Image plane - use image opacity */}
      {imageTexture && (
        <mesh
          // 0.999999 is to avoid z-fighting with the frustum lines.
          position={[0.0, 0.0, z * 0.999999]}
          rotation={new THREE.Euler(Math.PI, 0.0, 0.0)}
          castShadow={message.props.cast_shadow}
          receiveShadow={message.props.receive_shadow === true}
        >
          <planeGeometry
            attach="geometry"
            args={[message.props.aspect * y * 2, y * 2]}
          />
          <meshBasicMaterial
            attach="material"
            transparent={imageOpacity < 1.0}
            opacity={imageOpacity}
            side={THREE.DoubleSide}
            map={imageTexture}
            toneMapped={false}
          />
        </mesh>
      )}
      {children}
    </group>
  );
});
