import React, { useEffect } from 'react';
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

  useEffect(() => {
    onSceneReady?.();
  }, [onSceneReady]);

  return (
    <group name="TheCrossroadsWorld">
      <Lighting quality={quality} />

      <CameraController
        activePreset={cameraPreset}
        hoverFocus={activeHover}
        enableIdleMotion={quality.enableWindAnimation}
        onUserOrbit={onUserOrbit}
      />

      {/* Sculpted Floating Forest Diorama */}
      <group position={[0, -0.1, 0]}>
        <Terrain nodes={gltf.nodes} shadows={quality.shadows} />
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
