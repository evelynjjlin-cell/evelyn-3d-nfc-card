import React, { useMemo, useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

interface StreamProps {
  nodes: Record<string, THREE.Object3D>;
  enableWaterShader: boolean;
}

export const Stream: React.FC<StreamProps> = ({ nodes, enableWaterShader }) => {
  const waterMatRef = useRef<THREE.MeshStandardMaterial>(null);
  const rippleGroupRef = useRef<THREE.Group>(null);

  const waterGeo = useMemo(() => {
    const obj = nodes['Stream_Water'] as THREE.Mesh | undefined;
    return obj && obj.isMesh ? obj.geometry : null;
  }, [nodes]);

  const rippleLines = useMemo(
    () => [
      { x: -2.1, z: -0.32, rotY: -0.22, len: 0.45, phase: 0.0 },
      { x: -1.18, z: -0.02, rotY: -0.26, len: 0.48, phase: 1.4 },
      { x: 1.12, z: 0.50, rotY: -0.24, len: 0.46, phase: 2.6 },
      { x: 2.08, z: 0.82, rotY: -0.18, len: 0.42, phase: 3.9 },
    ],
    []
  );

  useFrame(({ clock }) => {
    if (!enableWaterShader) return;
    const t = clock.getElapsedTime();
    if (waterMatRef.current) {
      waterMatRef.current.roughness = 0.26 + 0.04 * Math.sin(t * 1.9);
    }
    if (rippleGroupRef.current) {
      rippleGroupRef.current.children.forEach((child, idx) => {
        const seed = rippleLines[idx];
        if (!seed) return;
        const drift = ((t * 0.22 + seed.phase) % 1.0) - 0.5;
        child.position.x = seed.x + drift * 0.3;
        child.scale.x = 0.85 + 0.22 * Math.sin(t * 2.2 + seed.phase);
      });
    }
  });

  return (
    <group name="WoodlandStreamGroup">
      {waterGeo && (
        <mesh name="Stream_Water" geometry={waterGeo} receiveShadow>
          <meshStandardMaterial
            ref={waterMatRef}
            color="#ffffff"
            vertexColors
            roughness={0.28}
            metalness={0.06}
            transparent
            opacity={0.92}
          />
        </mesh>
      )}

      {/* Subtle delicate current lines (no harsh white glare) */}
      <group ref={rippleGroupRef}>
        {rippleLines.map((r, i) => (
          <mesh
            key={i}
            position={[r.x, 0.028, r.z]}
            rotation={[-Math.PI / 2, 0, r.rotY]}
          >
            <planeGeometry args={[r.len, 0.022]} />
            <meshBasicMaterial color="#B5D4C8" transparent opacity={0.32} />
          </mesh>
        ))}
      </group>
    </group>
  );
};
