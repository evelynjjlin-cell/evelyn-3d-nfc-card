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
    const cobblesNode = nodes['Pathway_Cobbles'] as THREE.Mesh | undefined;
    const rawCobbleMat = cobblesNode?.material;
    const baseCobble = Array.isArray(rawCobbleMat) ? rawCobbleMat[0] : rawCobbleMat;
    let pathwayCobblesMat: THREE.MeshStandardMaterial;

    if (baseCobble && (baseCobble as THREE.MeshStandardMaterial).isMeshStandardMaterial) {
      pathwayCobblesMat = (baseCobble as THREE.MeshStandardMaterial).clone();
      pathwayCobblesMat.roughness = 0.78;
      pathwayCobblesMat.metalness = 0.02;
      pathwayCobblesMat.transparent = false;
      pathwayCobblesMat.depthWrite = true;
      pathwayCobblesMat.depthTest = true;
      pathwayCobblesMat.side = THREE.FrontSide;
      pathwayCobblesMat.vertexColors = false;
      if (pathwayCobblesMat.map) {
        pathwayCobblesMat.map.anisotropy = 8;
        pathwayCobblesMat.map.colorSpace = THREE.SRGBColorSpace;
      }
    } else {
      pathwayCobblesMat = new THREE.MeshStandardMaterial({
        color: '#9C9488',
        roughness: 0.78,
        metalness: 0.02,
        bumpMap: grassBump,
        bumpScale: 0.014,
      });
    }

    return {
      grassTop: new THREE.MeshStandardMaterial({
        color: '#ffffff',
        vertexColors: true,
        roughness: 0.82,
        metalness: 0.01,
        bumpMap: grassBump,
        bumpScale: 0.022,
        transparent: false,
        depthWrite: true,
        depthTest: true,
        side: THREE.FrontSide,
      }),
      soilRim: new THREE.MeshStandardMaterial({
        color: '#ffffff',
        vertexColors: true,
        roughness: 0.86,
        metalness: 0.03,
        bumpMap: grassBump,
        bumpScale: 0.026,
        transparent: false,
        depthWrite: true,
        depthTest: true,
        side: THREE.FrontSide,
      }),
      rockUnderside: new THREE.MeshStandardMaterial({
        color: '#ffffff',
        vertexColors: true,
        roughness: 0.88,
        metalness: 0.04,
        bumpMap: grassBump,
        bumpScale: 0.032,
        transparent: false,
        depthWrite: true,
        depthTest: true,
        side: THREE.FrontSide,
      }),
      pathwayCobbles: pathwayCobblesMat,
    };
  }, [grassBump, nodes]);

  const getGeometry = (name: string): THREE.BufferGeometry | null => {
    const obj = nodes[name] as THREE.Mesh | undefined;
    return obj && obj.isMesh ? obj.geometry : null;
  };

  const grassGeo = getGeometry('Island_Terrain_Top');
  const soilGeo = getGeometry('Island_Soil_Rim');
  const rockGeo = getGeometry('Island_Rock_Underside');
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
          castShadow={shadows}
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
