import React, { useEffect, useMemo, useRef } from 'react';
import { useFrame, useThree } from '@react-three/fiber';
import * as THREE from 'three';
import { QualityPreset } from '../../config/personalConfig';
import { TimeOfDayPreset } from '../../utils/timeOfDay';

interface LightingProps {
  quality: QualityPreset;
  timePreset: TimeOfDayPreset;
}

export const Lighting: React.FC<LightingProps> = ({ quality, timePreset }) => {
  const { gl } = useThree();
  const sporesRef = useRef<THREE.InstancedMesh>(null);
  const dummy = useMemo(() => new THREE.Object3D(), []);

  useEffect(() => {
    gl.setClearColor(timePreset.clearColor, 1);
  }, [gl, timePreset.clearColor]);

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
      {/* Time-of-day atmospheric studio fog */}
      <fog attach="fog" args={[timePreset.clearColor, 26, 46]} />

      {/* Balanced ambient base tuned to America/Toronto time of day */}
      <ambientLight intensity={timePreset.ambientIntensity} color={timePreset.ambientColor} />

      {/* Sky-to-moss hemisphere bounce fill */}
      <hemisphereLight
        args={[timePreset.hemiSkyColor, timePreset.hemiGroundColor, timePreset.hemiIntensity]}
        position={[0, 12, 0]}
      />

      {/* Key Light: Time-of-day sun or moonlight */}
      <directionalLight
        position={timePreset.sunPosition}
        intensity={timePreset.sunIntensity}
        color={timePreset.sunColor}
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

      {/* Secondary atmospheric fill keeping shadows luminous and readable */}
      <directionalLight
        position={timePreset.fillPosition}
        intensity={timePreset.fillIntensity}
        color={timePreset.fillColor}
      />

      {/* Rim backlight separating tree canopies from the background */}
      <directionalLight
        position={timePreset.rimPosition}
        intensity={timePreset.rimIntensity}
        color={timePreset.rimColor}
      />

      {/* Dedicated low-angle creek water specular glint light */}
      <directionalLight
        position={[-1.4, 4.8, -5.2]}
        intensity={timePreset.waterGlintIntensity * 0.65}
        color={timePreset.waterGlintColor}
      />

      {/* Warm crossroads lantern fill during Golden Hour & Evening/Night so signs, bridge & mailbox stay inviting */}
      {timePreset.lanternIntensity > 0.01 && (
        <pointLight
          position={[0.0, 1.75, 0.25]}
          intensity={timePreset.lanternIntensity}
          color={timePreset.lanternColor}
          distance={7.5}
          decay={1.4}
        />
      )}

      {/* Subtle soft ground shadow beneath the floating island */}
      <mesh position={[0, -2.55, 0]} rotation={[-Math.PI / 2, 0, 0]} receiveShadow={false}>
        <circleGeometry args={[3.3, 48]} />
        <meshBasicMaterial color="#0A1916" transparent opacity={0.22} />
      </mesh>

      {/* Restrained ambient forest dust / firefly motes */}
      {sporeSeeds.length > 0 && (
        <instancedMesh
          ref={sporesRef}
          args={[undefined, undefined, sporeSeeds.length]}
          frustumCulled={false}
        >
          <sphereGeometry args={[1, 8, 8]} />
          <meshBasicMaterial
            color={timePreset.sporeColor}
            transparent
            opacity={timePreset.sporeOpacity}
          />
        </instancedMesh>
      )}
    </group>
  );
};
