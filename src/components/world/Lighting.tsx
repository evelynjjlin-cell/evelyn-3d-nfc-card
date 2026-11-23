import React, { useMemo, useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { QualityPreset } from '../../config/personalConfig';

interface LightingProps {
  quality: QualityPreset;
}

export const Lighting: React.FC<LightingProps> = ({ quality }) => {
  const sporesRef = useRef<THREE.InstancedMesh>(null);
  const dummy = useMemo(() => new THREE.Object3D(), []);

  const sporeSeeds = useMemo(() => {
    const count = Math.min(24, quality.particlesCount);
    return Array.from({ length: count }, (_, idx) => {
      const angle = (idx / Math.max(1, count)) * Math.PI * 2 + (idx % 5) * 0.4;
      const radius = 0.8 + ((idx * 1.37) % 3.0);
      return {
        x: Math.cos(angle) * radius,
        y: 0.55 + ((idx * 0.43) % 2.0),
        z: Math.sin(angle) * (radius * 0.72),
        speed: 0.32 + (idx % 7) * 0.07,
        phase: idx * 1.13,
        scale: 0.013 + (idx % 4) * 0.004,
      };
    });
  }, [quality.particlesCount]);

  useFrame(({ clock }) => {
    if (!sporesRef.current) return;
    const t = clock.getElapsedTime();
    sporeSeeds.forEach((seed, i) => {
      const yOffset = quality.enableWindAnimation
        ? Math.sin(t * seed.speed + seed.phase) * 0.12
        : 0;
      const xOffset = quality.enableWindAnimation
        ? Math.cos(t * seed.speed * 0.7 + seed.phase) * 0.07
        : 0;
      dummy.position.set(seed.x + xOffset, seed.y + yOffset, seed.z);
      const pulse = quality.enableWindAnimation
        ? seed.scale * (0.85 + 0.22 * Math.sin(t * 1.6 + seed.phase))
        : seed.scale;
      dummy.scale.setScalar(pulse);
      dummy.updateMatrix();
      sporesRef.current!.setMatrixAt(i, dummy.matrix);
    });
    sporesRef.current.instanceMatrix.needsUpdate = true;
  });

  return (
    <group name="CrossroadsLighting">
      {/* Warm luminous forest studio fog */}
      <fog attach="fog" args={['#173229', 26, 46]} />

      {/* Balanced ambient base */}
      <ambientLight intensity={0.68} color="#EAF2E8" />

      {/* Warm sunlit sky to deep woodland moss hemisphere fill */}
      <hemisphereLight args={['#FAF5E6', '#2A4839', 1.05]} position={[0, 12, 0]} />

      {/* Key Light: Warm late-afternoon sun */}
      <directionalLight
        position={[7.2, 11.2, 6.4]}
        intensity={2.25}
        color="#FFF0CE"
        castShadow={quality.shadows}
        shadow-mapSize-width={quality.shadowMapSize}
        shadow-mapSize-height={quality.shadowMapSize}
        shadow-camera-near={1}
        shadow-camera-far={28}
        shadow-camera-left={-5.8}
        shadow-camera-right={5.8}
        shadow-camera-top={5.8}
        shadow-camera-bottom={-5.8}
        shadow-bias={-0.0004}
      />

      {/* Cool sage fill from the west so shadows stay luminous and readable */}
      <directionalLight position={[-6.8, 6.0, 4.2]} intensity={0.82} color="#C2DFCE" />

      {/* Soft golden rim backlight separating tree canopies from the background */}
      <directionalLight position={[-1.2, 7.5, -8.0]} intensity={0.78} color="#FFE4B5" />

      {/* Subtle, restrained soft ground shadow beneath the floating island (no heavy black disc) */}
      <mesh position={[0, -2.55, 0]} rotation={[-Math.PI / 2, 0, 0]} receiveShadow={false}>
        <circleGeometry args={[3.3, 48]} />
        <meshBasicMaterial color="#0D1F19" transparent opacity={0.22} />
      </mesh>

      {/* Restrained ambient golden dust motes */}
      {sporeSeeds.length > 0 && (
        <instancedMesh
          ref={sporesRef}
          args={[undefined, undefined, sporeSeeds.length]}
          frustumCulled={false}
        >
          <sphereGeometry args={[1, 8, 8]} />
          <meshBasicMaterial color="#F6E6BC" transparent opacity={0.52} />
        </instancedMesh>
      )}
    </group>
  );
};
