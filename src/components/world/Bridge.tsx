import React, { useMemo } from 'react';
import * as THREE from 'three';
import {
  getWoodGrainAlbedoTexture,
  getWoodGrainTexture,
  getWoodRoughnessTexture,
} from '../../utils/proceduralTextures';

interface BridgeProps {
  nodes: Record<string, THREE.Object3D>;
  shadows: boolean;
}

export const Bridge: React.FC<BridgeProps> = ({ nodes, shadows }) => {
  const woodBump = useMemo(() => getWoodGrainTexture(), []);
  const woodAlbedo = useMemo(() => getWoodGrainAlbedoTexture(), []);
  const woodRoughness = useMemo(() => getWoodRoughnessTexture(), []);

  const bridgeMat = useMemo(
    () =>
      new THREE.MeshStandardMaterial({
        color: '#ffffff',
        vertexColors: true,
        map: woodAlbedo,
        roughnessMap: woodRoughness,
        roughness: 0.78,
        metalness: 0.02,
        bumpMap: woodBump,
        bumpScale: 0.022,
        transparent: false,
        opacity: 1.0,
        depthWrite: true,
        depthTest: true,
        side: THREE.FrontSide,
      }),
    [woodAlbedo, woodBump, woodRoughness]
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
