import React, { useMemo, useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { getWaterRippleBumpTexture } from '../../utils/proceduralTextures';
import { TimeOfDayPreset } from '../../utils/timeOfDay';

interface StreamProps {
  nodes: Record<string, THREE.Object3D>;
  enableWaterShader: boolean;
  timePreset: TimeOfDayPreset;
}

export const Stream: React.FC<StreamProps> = ({ nodes, enableWaterShader, timePreset }) => {
  const waterMatRef = useRef<THREE.MeshPhysicalMaterial>(null);
  const rippleGroupRef = useRef<THREE.Group>(null);
  const waterRippleBump = useMemo(() => getWaterRippleBumpTexture(), []);

  const bedGeo = useMemo(() => {
    const obj = nodes['Stream_Bed'] as THREE.Mesh | undefined;
    return obj && obj.isMesh ? obj.geometry : null;
  }, [nodes]);

  const waterGeo = useMemo(() => {
    const obj = nodes['Stream_Water'] as THREE.Mesh | undefined;
    return obj && obj.isMesh ? obj.geometry : null;
  }, [nodes]);

  const rippleLines = useMemo(
    () => [
      { x: -2.45, z: -0.36, rotY: -0.22, len: 0.62, width: 0.036, phase: 0.0, isGlint: true },
      { x: -1.78, z: -0.18, rotY: -0.25, len: 0.72, width: 0.044, phase: 0.8, isGlint: false },
      { x: -1.25, z: -0.02, rotY: -0.26, len: 0.68, width: 0.038, phase: 1.6, isGlint: true },
      { x: -0.76, z: 0.12, rotY: -0.23, len: 0.64, width: 0.042, phase: 2.3, isGlint: false },
      { x: -0.46, z: 0.22, rotY: -0.20, len: 0.52, width: 0.034, phase: 3.0, isGlint: true },
      { x: 0.56, z: 0.30, rotY: -0.24, len: 0.66, width: 0.042, phase: 3.7, isGlint: true },
      { x: 0.98, z: 0.44, rotY: -0.23, len: 0.70, width: 0.038, phase: 4.4, isGlint: false },
      { x: 1.48, z: 0.60, rotY: -0.22, len: 0.64, width: 0.044, phase: 5.1, isGlint: true },
      { x: 1.98, z: 0.74, rotY: -0.19, len: 0.58, width: 0.036, phase: 5.8, isGlint: false },
      { x: 2.42, z: 0.86, rotY: -0.17, len: 0.50, width: 0.032, phase: 6.4, isGlint: true },
    ],
    []
  );

  useFrame(({ clock }) => {
    if (!enableWaterShader) return;
    const t = clock.getElapsedTime();
    waterRippleBump.offset.x = (t * 0.08) % 1.0;
    waterRippleBump.offset.y = Math.sin(t * 0.35) * 0.06;

    if (waterMatRef.current) {
      waterMatRef.current.roughness = 0.21 + 0.03 * Math.sin(t * 2.0);
      waterMatRef.current.emissiveIntensity =
        timePreset.waterEmissiveIntensity + 0.04 * Math.sin(t * 1.6);
    }
    if (rippleGroupRef.current) {
      rippleGroupRef.current.children.forEach((child, idx) => {
        const seed = rippleLines[idx];
        if (!seed) return;
        const drift = ((t * 0.26 + seed.phase) % 1.0) - 0.5;
        child.position.x = seed.x + drift * 0.32;
        child.scale.x = 0.84 + 0.26 * Math.sin(t * 2.3 + seed.phase);
      });
    }
  });

  return (
    <group name="WoodlandStreamGroup">
      {/* Dedicated localized water shimmer lights along the left and right creek pools */}
      <pointLight
        position={[-1.25, 0.85, 0.25]}
        intensity={timePreset.waterGlintIntensity * 0.55}
        color={timePreset.waterGlintColor}
        distance={3.6}
        decay={1.6}
      />
      <pointLight
        position={[1.35, 0.85, 0.65]}
        intensity={timePreset.waterGlintIntensity * 0.55}
        color={timePreset.waterGlintColor}
        distance={3.6}
        decay={1.6}
      />

      {/* Sculpted Pebble Riverbed visible beneath the luminous translucent water */}
      {bedGeo && (
        <mesh name="Stream_Bed" geometry={bedGeo} receiveShadow>
          <meshStandardMaterial
            color="#D6ECE6"
            vertexColors
            roughness={0.78}
            metalness={0.04}
            emissive="#103A38"
            emissiveIntensity={0.14}
          />
        </mesh>
      )}

      {/* Widened Luminous Creek Water with Clearcoat Specular Reflection & Wavelet Shimmer */}
      {waterGeo && (
        <mesh name="Stream_Water" geometry={waterGeo} receiveShadow>
          <meshPhysicalMaterial
            ref={waterMatRef}
            color="#E2FAF6"
            vertexColors
            roughness={0.21}
            metalness={0.08}
            clearcoat={0.92}
            clearcoatRoughness={0.12}
            ior={1.333}
            reflectivity={0.92}
            bumpMap={waterRippleBump}
            bumpScale={0.022}
            emissive={timePreset.waterEmissiveColor}
            emissiveIntensity={timePreset.waterEmissiveIntensity}
            transparent
            opacity={0.85}
          />
        </mesh>
      )}

      {/* Luminous Specular Current Shimmer & Caustic Highlights */}
      <group ref={rippleGroupRef}>
        {rippleLines.map((r, i) => (
          <mesh
            key={i}
            position={[r.x, 0.064, r.z]}
            rotation={[-Math.PI / 2, 0, r.rotY]}
          >
            <planeGeometry args={[r.len, r.width]} />
            <meshBasicMaterial
              color={r.isGlint ? timePreset.waterRippleHighlightColor : '#AEECE2'}
              transparent
              opacity={r.isGlint ? 0.58 : 0.36}
            />
          </mesh>
        ))}
      </group>
    </group>
  );
};
