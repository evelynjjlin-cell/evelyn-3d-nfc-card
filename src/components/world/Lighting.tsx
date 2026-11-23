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
    const count = quality.particlesCount;
    return Array.from({ length: count }, (_, idx) => {
      const angle = (idx / Math.max(1, count)) * Math.PI * 2 + (idx % 5) * 0.4;
      const radius = 0.7 + ((idx * 1.37) % 3.1);
      return {
        x: Math.cos(angle) * radius,
        y: 0.45 + ((idx * 0.43) % 2.1),
        z: Math.sin(angle) * (radius * 0.72),
        speed: 0.35 + (idx % 7) * 0.08,
        phase: idx * 1.13,
        scale: 0.016 + (idx % 4) * 0.005,
      };
    });
  }, [quality.particlesCount]);

  useFrame(({ clock }) => {
    if (!sporesRef.current) return;
    const t = clock.getElapsedTime();
    sporeSeeds.forEach((seed, i) => {
      const yOffset = quality.enableWindAnimation
        ? Math.sin(t * seed.speed + seed.phase) * 0.14
        : 0;
      const xOffset = quality.enableWindAnimation
        ? Math.cos(t * seed.speed * 0.7 + seed.phase) * 0.08
        : 0;
      dummy.position.set(seed.x + xOffset, seed.y + yOffset, seed.z);
      const pulse = quality.enableWindAnimation
        ? seed.scale * (0.82 + 0.25 * Math.sin(t * 1.8 + seed.phase))
        : seed.scale;
      dummy.scale.setScalar(pulse);
      dummy.updateMatrix();
      sporesRef.current!.setMatrixAt(i, dummy.matrix);
    });
    sporesRef.current.instanceMatrix.needsUpdate = true;
  });

  return (
    <group name="CrossroadsLighting">
      {/* Soft atmospheric depth fog matching deep forest background */}
      <fog attach="fog" args={['#132922', 24.5, 42]} />

      {/* Gentle ambient base */}
      <ambientLight intensity={0.62} color="#E8F0E6" />

      {/* Sky-to-moss hemisphere fill for rich organic shading in crevices */}
      <hemisphereLight args={['#F4F2E6', '#263E31', 0.92]} position={[0, 10, 0]} />

      {/* Warm late-afternoon directional sunlight */}
      <directionalLight
        position={[6.8, 10.5, 6.2]}
        intensity={2.15}
        color="#FFF0CF"
        castShadow={quality.shadows}
        shadow-mapSize-width={quality.shadowMapSize}
        shadow-mapSize-height={quality.shadowMapSize}
        shadow-camera-near={1}
        shadow-camera-far={26}
        shadow-camera-left={-5.8}
        shadow-camera-right={5.8}
        shadow-camera-top={5.8}
        shadow-camera-bottom={-5.8}
        shadow-bias={-0.0005}
      />

      {/* Cool sage fill light from opposite side so shadows stay readable */}
      <directionalLight position={[-6.2, 5.4, 3.8]} intensity={0.72} color="#B8D4C2" />

      {/* Golden rim backlight to highlight tree canopy silhouettes */}
      <directionalLight position={[0.0, 6.5, -7.5]} intensity={0.68} color="#FFE2B3" />

      {/* Warm spotlight accent bathing the central crossroads, signs, and mailbox */}
      <pointLight position={[0, 3.2, 1.2]} intensity={0.85} distance={8.5} color="#FFF3D6" />

      {/* Soft studio shadow-pedestal disc beneath the floating island */}
      <mesh position={[0, -2.55, 0]} rotation={[-Math.PI / 2, 0, 0]} receiveShadow={false}>
        <circleGeometry args={[4.4, 48]} />
        <meshBasicMaterial color="#0A1713" transparent opacity={0.48} />
      </mesh>

      {/* Subtle golden forest spores floating in the sunbeams */}
      {sporeSeeds.length > 0 && (
        <instancedMesh
          ref={sporesRef}
          args={[undefined, undefined, sporeSeeds.length]}
          frustumCulled={false}
        >
          <sphereGeometry args={[1, 8, 8]} />
          <meshBasicMaterial color="#F6E6BC" transparent opacity={0.68} />
        </instancedMesh>
      )}
    </group>
  );
};
