import React, { useMemo } from 'react';
import * as THREE from 'three';
import { getGrassBumpTexture } from '../../utils/proceduralTextures';

interface TerrainProps {
  nodes: Record<string, THREE.Object3D>;
  shadows: boolean;
}

export const Terrain: React.FC<TerrainProps> = ({ nodes, shadows }) => {
  const grassBump = useMemo(() => getGrassBumpTexture(), []);

  const materials = useMemo(() => {
    return {
      grassTop: new THREE.MeshStandardMaterial({
        color: '#5B7854',
        roughness: 0.82,
        metalness: 0.02,
        bumpMap: grassBump,
        bumpScale: 0.018,
      }),
      soilRim: new THREE.MeshStandardMaterial({
        color: '#7E5C43',
        roughness: 0.86,
        metalness: 0.02,
        bumpMap: grassBump,
        bumpScale: 0.022,
      }),
      rockUnderside: new THREE.MeshStandardMaterial({
        color: '#4E4740',
        roughness: 0.88,
        metalness: 0.05,
        bumpMap: grassBump,
        bumpScale: 0.028,
      }),
      pathwayEarth: new THREE.MeshStandardMaterial({
        color: '#C2A37A',
        roughness: 0.84,
        metalness: 0.01,
        bumpMap: grassBump,
        bumpScale: 0.014,
      }),
      pathwayCobbles: new THREE.MeshStandardMaterial({
        color: '#958D81',
        roughness: 0.74,
        metalness: 0.04,
      }),
    };
  }, [grassBump]);

  const getGeometry = (name: string): THREE.BufferGeometry | null => {
    const obj = nodes[name] as THREE.Mesh | undefined;
    return obj && obj.isMesh ? obj.geometry : null;
  };

  const grassGeo = getGeometry('Island_Terrain_Top');
  const soilGeo = getGeometry('Island_Soil_Rim');
  const rockGeo = getGeometry('Island_Rock_Underside');
  const pathGeo = getGeometry('Crossroads_Pathway');
  const cobblesGeo = getGeometry('Pathway_Cobbles');

  return (
    <group name="IslandTerrainGroup">
      {grassGeo && (
        <mesh
          name="Island_Terrain_Top"
          geometry={grassGeo}
          material={materials.grassTop}
          receiveShadow={shadows}
          castShadow={shadows}
        />
      )}
      {soilGeo && (
        <mesh
          name="Island_Soil_Rim"
          geometry={soilGeo}
          material={materials.soilRim}
          receiveShadow={shadows}
          castShadow={shadows}
        />
      )}
      {rockGeo && (
        <mesh
          name="Island_Rock_Underside"
          geometry={rockGeo}
          material={materials.rockUnderside}
          receiveShadow={shadows}
        />
      )}
      {pathGeo && (
        <mesh
          name="Crossroads_Pathway"
          geometry={pathGeo}
          material={materials.pathwayEarth}
          receiveShadow={shadows}
        />
      )}
      {cobblesGeo && (
        <mesh
          name="Pathway_Cobbles"
          geometry={cobblesGeo}
          material={materials.pathwayCobbles}
          receiveShadow={shadows}
          castShadow={shadows}
        />
      )}
    </group>
  );
};
