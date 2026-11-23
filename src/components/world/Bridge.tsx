import React, { useMemo } from 'react';
import * as THREE from 'three';
import { getWoodGrainTexture } from '../../utils/proceduralTextures';

interface BridgeProps {
  nodes: Record<string, THREE.Object3D>;
  shadows: boolean;
}

export const Bridge: React.FC<BridgeProps> = ({ nodes, shadows }) => {
  const woodBump = useMemo(() => getWoodGrainTexture(), []);

  const bridgeMat = useMemo(
    () =>
      new THREE.MeshStandardMaterial({
        color: '#ffffff',
        vertexColors: true,
        roughness: 0.65,
        metalness: 0.04,
        bumpMap: woodBump,
        bumpScale: 0.018,
      }),
    [woodBump]
  );

  const bridgeGeo = useMemo(() => {
    const obj = nodes['Wooden_Bridge'] as THREE.Mesh | undefined;
    return obj && obj.isMesh ? obj.geometry : null;
  }, [nodes]);

  return (
    <group name="WoodenBridgeGroup">
      {bridgeGeo && (
        <mesh
          name="Wooden_Bridge"
          geometry={bridgeGeo}
          material={bridgeMat}
          castShadow={shadows}
          receiveShadow={shadows}
        />
      )}
    </group>
  );
};
