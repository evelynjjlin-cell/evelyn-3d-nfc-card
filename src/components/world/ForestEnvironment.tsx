import React, { useEffect, useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { useGLTF } from '@react-three/drei';
import * as THREE from 'three';
import { CameraViewPreset, QualityPreset } from '../../config/personalConfig';
import { Lighting } from './Lighting';
import { Terrain } from './Terrain';
import { Stream } from './Stream';
import { Bridge } from './Bridge';
import { TreesAndVegetation } from './TreesAndVegetation';
import { WoodenSigns, SignId } from './WoodenSigns';
import { Mailbox } from './Mailbox';
import { IdentityPlaque3D } from './IdentityPlaque3D';
import { CameraController } from './CameraController';

const MODEL_PATH = '/models/crossroads_environment.glb';

interface ForestEnvironmentProps {
  quality: QualityPreset;
  cameraPreset: CameraViewPreset['id'];
  activeHover: string | null;
  isMailboxOpen: boolean;
  onHoverChange: (id: string | null) => void;
  onSelectSign: (id: SignId) => void;
  onSelectMailbox: () => void;
  onSceneReady?: () => void;
  onUserOrbit?: () => void;
}

export const ForestEnvironment: React.FC<ForestEnvironmentProps> = ({
  quality,
  cameraPreset,
  activeHover,
  isMailboxOpen,
  onHoverChange,
  onSelectSign,
  onSelectMailbox,
  onSceneReady,
  onUserOrbit,
}) => {
  const gltf = useGLTF(MODEL_PATH) as unknown as {
    nodes: Record<string, THREE.Object3D>;
  };

  const collectibleGroupRef = useRef<THREE.Group>(null);
  const introStartRef = useRef<number | null>(null);

  useEffect(() => {
    onSceneReady?.();
  }, [onSceneReady]);

  // Gentle introductory settling motion + subtle suspended collectible breathing
  useFrame(({ clock }) => {
    if (!collectibleGroupRef.current) return;
    if (!quality.enableWindAnimation) {
      collectibleGroupRef.current.position.y = -0.18;
      return;
    }
    const t = clock.getElapsedTime();
    if (introStartRef.current === null) {
      introStartRef.current = t;
    }
    const elapsed = t - introStartRef.current;
    // Damped introductory settle over first 1.1 seconds
    const settleOffset = elapsed < 1.1 ? Math.exp(-elapsed * 4.2) * 0.14 : 0;
    const breathOffset = Math.sin(t * 1.15) * 0.016;
    collectibleGroupRef.current.position.y = -0.18 - settleOffset + breathOffset;
  });

  return (
    <group name="TheCrossroadsWorld">
      <Lighting quality={quality} />

      <CameraController
        activePreset={cameraPreset}
        hoverFocus={activeHover}
        enableIdleMotion={quality.enableWindAnimation}
        onUserOrbit={onUserOrbit}
      />

      {/* Sculpted Floating Forest Collectible with Physically Embedded 3D Identity Plaque */}
      <group ref={collectibleGroupRef} position={[0, -0.18, 0]}>
        <Terrain nodes={gltf.nodes} shadows={quality.shadows} />
        <IdentityPlaque3D
          nodes={gltf.nodes}
          shadows={quality.shadows}
          onSelectPlaque={onSelectMailbox}
        />
        <Stream nodes={gltf.nodes} enableWaterShader={quality.enableWaterShader} />
        <Bridge nodes={gltf.nodes} shadows={quality.shadows} />
        <TreesAndVegetation nodes={gltf.nodes} quality={quality} />
        <WoodenSigns
          nodes={gltf.nodes}
          shadows={quality.shadows}
          activeHover={activeHover}
          onHoverChange={onHoverChange}
          onSelectSign={onSelectSign}
        />
        <Mailbox
          nodes={gltf.nodes}
          shadows={quality.shadows}
          isOpen={isMailboxOpen}
          activeHover={activeHover}
          onHoverChange={onHoverChange}
          onSelectMailbox={onSelectMailbox}
        />
      </group>
    </group>
  );
};

useGLTF.preload(MODEL_PATH);
