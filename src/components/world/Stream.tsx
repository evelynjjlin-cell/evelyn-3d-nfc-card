import React, { useMemo, useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

interface StreamProps {
  nodes: Record<string, THREE.Object3D>;
  enableWaterShader: boolean;
}

export const Stream: React.FC<StreamProps> = ({ nodes, enableWaterShader }) => {
  const waterMatRef = useRef<THREE.MeshPhysicalMaterial>(null);
  const rippleGroupRef = useRef<THREE.Group>(null);

  const waterGeo = useMemo(() => {
    const obj = nodes['Stream_Water'] as THREE.Mesh | undefined;
    return obj && obj.isMesh ? obj.geometry : null;
  }, [nodes]);

  const rippleLines = useMemo(
    () => [
      { x: -2.2, z: -0.35, rotY: -0.22, len: 0.55, phase: 0.0 },
      { x: -1.25, z: -0.02, rotY: -0.28, len: 0.62, phase: 1.4 },
      { x: 1.15, z: 0.52, rotY: -0.25, len: 0.58, phase: 2.6 },
      { x: 2.15, z: 0.85, rotY: -0.18, len: 0.52, phase: 3.9 },
    ],
    []
  );

  useFrame(({ clock }) => {
    if (!enableWaterShader) return;
    const t = clock.getElapsedTime();
    if (waterMatRef.current) {
      waterMatRef.current.roughness = 0.14 + 0.04 * Math.sin(t * 2.1);
      waterMatRef.current.emissiveIntensity = 0.12 + 0.05 * Math.sin(t * 1.6);
    }
    if (rippleGroupRef.current) {
      rippleGroupRef.current.children.forEach((child, idx) => {
        const seed = rippleLines[idx];
        if (!seed) return;
        const drift = ((t * 0.25 + seed.phase) % 1.0) - 0.5;
        child.position.x = seed.x + drift * 0.35;
        child.scale.x = 0.85 + 0.25 * Math.sin(t * 2.4 + seed.phase);
      });
    }
  });

  return (
    <group name="WoodlandStreamGroup">
      {waterGeo && (
        <mesh name="Stream_Water" geometry={waterGeo} receiveShadow>
          <meshPhysicalMaterial
            ref={waterMatRef}
            color="#3D8A92"
            emissive="#1C5058"
            emissiveIntensity={0.14}
            roughness={0.15}
            metalness={0.08}
            transmission={0.18}
            thickness={0.4}
            clearcoat={0.85}
            clearcoatRoughness={0.15}
          />
        </mesh>
      )}

      {/* Subtle stylized surface foam/shimmer streaks */}
      <group ref={rippleGroupRef}>
        {rippleLines.map((r, i) => (
          <mesh
            key={i}
            position={[r.x, 0.035, r.z]}
            rotation={[-Math.PI / 2, 0, r.rotY]}
          >
            <planeGeometry args={[r.len, 0.032]} />
            <meshBasicMaterial color="#D6F0EE" transparent opacity={0.45} />
          </mesh>
        ))}
      </group>
    </group>
  );
};
