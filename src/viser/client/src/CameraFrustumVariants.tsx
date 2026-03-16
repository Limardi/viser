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
    
    // Create cylinder geometry with more segments for smoother appearance
    return new THREE.CylinderGeometry(radius, radius, length, 8, 1);
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

  // Clean up geometry on unmount
  React.useEffect(() => {
    return () => {
      geometry.dispose();
    };
  }, [geometry]);

  return (
    <mesh geometry={geometry} position={position} rotation={rotation}>
      <meshBasicMaterial
        attach="material"
        color={color}
        transparent={true}
        opacity={opacity}
        depthWrite={false}
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

  // Split frustum into separate parts for different colors
  const framePoints: [number, number, number][] = [
    // Rectangle at the far plane.
    [-1, -1, 1],
    [1, -1, 1],
    [1, -1, 1],
    [1, 1, 1],
    [1, 1, 1],
    [-1, 1, 1],
    [-1, 1, 1],
    [-1, -1, 1],
  ].map((xyz) => [xyz[0] * x, xyz[1] * y, xyz[2] * z]);

  const rayPoints: [number, number, number][] = [
    // Lines from corners to origin.
    [-1, -1, 1],
    [0, 0, 0],
    [0, 0, 0],
    [1, -1, 1],
    [-1, 1, 1],
    [0, 0, 0],
    [0, 0, 0],
    [1, 1, 1],
  ].map((xyz) => [xyz[0] * x, xyz[1] * y, xyz[2] * z]);

  const upIndicatorPoints: [number, number, number][] = [
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

  const lineOpacity = message.props.line_opacity ?? message.props.opacity ?? 1.0;
  const imageOpacity = message.props.opacity ?? 1.0;
  const lineStyle = message.props.line_style ?? "flat";
  const lineRadius = message.props.line_radius ?? 0.01;

  const frameOpacity = message.props.frame_opacity ?? lineOpacity;
  const rayOpacity = message.props.ray_opacity ?? lineOpacity;

  const frameColor = message.props.frame_color
    ? new THREE.Color().setRGB(
        message.props.frame_color[0] / 255,
        message.props.frame_color[1] / 255,
        message.props.frame_color[2] / 255,
      )
    : color;

  const rayColor = message.props.ray_color
    ? new THREE.Color().setRGB(
        message.props.ray_color[0] / 255,
        message.props.ray_color[1] / 255,
        message.props.ray_color[2] / 255,
      )
    : color;

  // Generate line segments for tube rendering
  const frameSegments = React.useMemo(() => {
    const segments: Array<[[number, number, number], [number, number, number]]> = [];
    for (let i = 0; i < framePoints.length; i += 2) {
      if (i + 1 < framePoints.length) {
        segments.push([framePoints[i], framePoints[i + 1]]);
      }
    }
    return segments;
  }, [framePoints]);

  const raySegments = React.useMemo(() => {
    const segments: Array<[[number, number, number], [number, number, number]]> = [];
    for (let i = 0; i < rayPoints.length; i += 2) {
      if (i + 1 < rayPoints.length) {
        segments.push([rayPoints[i], rayPoints[i + 1]]);
      }
    }
    return segments;
  }, [rayPoints]);

  const upIndicatorSegments = React.useMemo(() => {
    const segments: Array<[[number, number, number], [number, number, number]]> = [];
    for (let i = 0; i < upIndicatorPoints.length; i += 2) {
      if (i + 1 < upIndicatorPoints.length) {
        segments.push([upIndicatorPoints[i], upIndicatorPoints[i + 1]]);
      }
    }
    return segments;
  }, [upIndicatorPoints]);

  const isImageOnly = message.props.variant === "image_only";
  const showFrame = message.props.show_frame;
  const showAxes = message.props.show_axes;

  // image_only: image always at origin so node position = image center.
  // wireframe/filled: image at far plane.
  const imageZ = isImageOnly ? 0.0 : z * 0.999999;

  // Border slightly in front of image to avoid z-fighting.
  const borderZ = isImageOnly ? -0.001 * z : z * 0.998;
  const borderPoints: [number, number, number][] = [
    [-x, -y, borderZ],
    [x, -y, borderZ],
    [x, -y, borderZ],
    [x, y, borderZ],
    [x, y, borderZ],
    [-x, y, borderZ],
    [-x, y, borderZ],
    [-x, -y, borderZ],
  ];

  const borderSegments = React.useMemo(() => {
    const segments: Array<
      [[number, number, number], [number, number, number]]
    > = [];
    for (let i = 0; i < borderPoints.length; i += 2) {
      if (i + 1 < borderPoints.length) {
        segments.push([borderPoints[i], borderPoints[i + 1]]);
      }
    }
    return segments;
  }, [borderPoints]);

  // Up indicator for show_axes: at origin z for image_only, at far plane for others.
  const axesUpPoints: [number, number, number][] = isImageOnly
    ? [
        [0.0, -1.2, 0.0],
        [0.0, -1.0, 0.0],
      ].map((xyz) => [xyz[0] * x, xyz[1] * y, xyz[2]])
    : upIndicatorPoints;

  const axesUpSegments = React.useMemo(() => {
    const segments: Array<
      [[number, number, number], [number, number, number]]
    > = [];
    for (let i = 0; i < axesUpPoints.length; i += 2) {
      if (i + 1 < axesUpPoints.length) {
        segments.push([axesUpPoints[i], axesUpPoints[i + 1]]);
      }
    }
    return segments;
  }, [axesUpPoints]);

  return (
    <group ref={ref}>
      {/* Full frustum wireframe: frame + rays + up indicator.
          Only for wireframe/filled variants (not image_only). */}
      {!isImageOnly &&
        (lineStyle === "flat" ? (
          <>
            <Line
              points={framePoints}
              color={
                isHovered
                  ? 0xfbff00
                  : rgbToInt(
                      message.props.frame_color ?? message.props.color,
                    )
              }
              lineWidth={
                isHovered
                  ? 1.5 * message.props.line_width
                  : message.props.line_width
              }
              segments
              opacity={frameOpacity}
              transparent={frameOpacity < 1.0}
            />
            <Line
              points={rayPoints}
              color={
                isHovered
                  ? 0xfbff00
                  : rgbToInt(message.props.ray_color ?? message.props.color)
              }
              lineWidth={
                isHovered
                  ? 1.5 * message.props.line_width
                  : message.props.line_width
              }
              segments
              opacity={rayOpacity}
              transparent={rayOpacity < 1.0}
            />
            <Line
              points={upIndicatorPoints}
              color={isHovered ? 0xfbff00 : rgbToInt(message.props.color)}
              lineWidth={
                isHovered
                  ? 1.5 * message.props.line_width
                  : message.props.line_width
              }
              segments
              opacity={lineOpacity}
              transparent={lineOpacity < 1.0}
            />
          </>
        ) : (
          <>
            {frameSegments.map((segment, idx) => (
              <LineTube
                key={`frame-${idx}`}
                start={segment[0]}
                end={segment[1]}
                radius={lineRadius}
                color={isHovered ? 0xfbff00 : frameColor}
                opacity={frameOpacity}
              />
            ))}
            {raySegments.map((segment, idx) => (
              <LineTube
                key={`ray-${idx}`}
                start={segment[0]}
                end={segment[1]}
                radius={lineRadius}
                color={isHovered ? 0xfbff00 : rayColor}
                opacity={rayOpacity}
              />
            ))}
            {upIndicatorSegments.map((segment, idx) => (
              <LineTube
                key={`up-${idx}`}
                start={segment[0]}
                end={segment[1]}
                radius={lineRadius}
                color={isHovered ? 0xfbff00 : color}
                opacity={lineOpacity}
              />
            ))}
          </>
        ))}

      {/* show_frame: 4-edge image border, slightly in front of the image. */}
      {showFrame &&
        (lineStyle === "flat" ? (
          <Line
            points={borderPoints}
            color={
              isHovered
                ? 0xfbff00
                : rgbToInt(
                    message.props.frame_color ?? message.props.color,
                  )
            }
            lineWidth={
              isHovered
                ? 1.5 * message.props.line_width
                : message.props.line_width
            }
            segments
            opacity={frameOpacity}
            transparent={frameOpacity < 1.0}
          />
        ) : (
          <>
            {borderSegments.map((segment, idx) => (
              <LineTube
                key={`border-${idx}`}
                start={segment[0]}
                end={segment[1]}
                radius={lineRadius}
                color={isHovered ? 0xfbff00 : frameColor}
                opacity={frameOpacity}
              />
            ))}
          </>
        ))}

      {/* show_axes: up direction indicator, same color as border. */}
      {showAxes &&
        (lineStyle === "flat" ? (
          <Line
            points={axesUpPoints}
            color={isHovered ? 0xfbff00 : rgbToInt(message.props.frame_color ?? message.props.color)}
            lineWidth={
              isHovered
                ? 1.5 * message.props.line_width
                : message.props.line_width
            }
            segments
            opacity={frameOpacity}
            transparent={frameOpacity < 1.0}
          />
        ) : (
          <>
            {axesUpSegments.map((segment, idx) => (
              <LineTube
                key={`axes-up-${idx}`}
                start={segment[0]}
                end={segment[1]}
                radius={lineRadius}
                color={isHovered ? 0xfbff00 : frameColor}
                opacity={frameOpacity}
              />
            ))}
          </>
        ))}

      {/* Filled faces - only for "filled" variant */}
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

      {/* Image plane */}
      {imageTexture && (
        <mesh
          position={[0.0, 0.0, imageZ]}
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
