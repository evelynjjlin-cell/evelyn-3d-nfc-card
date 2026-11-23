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
      { x: -2.2, z: -0.32, rotY: -0.22, len: 0.54, phase: 0.0 },
      { x: -1.35, z: -0.04, rotY: -0.26, len: 0.62, phase: 1.1 },
      { x: -0.58, z: 0.16, rotY: -0.22, len: 0.56, phase: 2.2 },
      { x: 0.62, z: 0.34, rotY: -0.24, len: 0.58, phase: 3.1 },
      { x: 1.38, z: 0.56, rotY: -0.22, len: 0.55, phase: 4.2 },
      { x: 2.15, z: 0.80, rotY: -0.18, len: 0.48, phase: 5.3 },
    ],
    []
  );

  useFrame(({ clock }) => {
    if (!enableWaterShader) return;
    const t = clock.getElapsedTime();
    if (waterMatRef.current) {
      waterMatRef.current.roughness = 0.22 + 0.04 * Math.sin(t * 1.8);
    }
    if (rippleGroupRef.current) {
      rippleGroupRef.current.children.forEach((child, idx) => {
        const seed = rippleLines[idx];
        if (!seed) return;
        const drift = ((t * 0.24 + seed.phase) % 1.0) - 0.5;
        child.position.x = seed.x + drift * 0.34;
        child.scale.x = 0.85 + 0.24 * Math.sin(t * 2.1 + seed.phase);
      });
    }
  });

  return (
    <group name="WoodlandStreamGroup">
      {/* Sculpted Pebble Riverbed visible beneath the translucent water */}
      {bedGeo && (
        <mesh name="Stream_Bed" geometry={bedGeo} receiveShadow>
          <meshStandardMaterial color="#ffffff" vertexColors roughness={0.85} metalness={0.02} />
        </mesh>
      )}

      {/* Widened Translucent Creek Water with Depth Variation & Soft Reflections */}
      {waterGeo && (
        <mesh name="Stream_Water" geometry={waterGeo} receiveShadow>
          <meshStandardMaterial
            ref={waterMatRef}
            color="#ffffff"
            vertexColors
            roughness={0.22}
            metalness={0.08}
            transparent
            opacity={0.86}
          />
        </mesh>
      )}

      {/* Gentle Flow Detail & Soft Current Ripples */}
      <group ref={rippleGroupRef}>
        {rippleLines.map((r, i) => (
          <mesh
            key={i}
            position={[r.x, 0.06, r.z]}
            rotation={[-Math.PI / 2, 0, r.rotY]}
          >
            <planeGeometry args={[r.len, 0.028]} />
            <meshBasicMaterial color="#CBE8DE" transparent opacity={0.38} />
          </mesh>
        ))}
      </group>
    </group>
  );
};
