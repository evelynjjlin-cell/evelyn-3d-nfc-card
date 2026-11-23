import React, { useMemo, useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { QualityPreset } from '../../config/personalConfig';

interface TreesAndVegetationProps {
  nodes: Record<string, THREE.Object3D>;
  quality: QualityPreset;
}

const TREE_DEFS = [
  { id: 'Tree_NW_Hero', phase: 0.0 },
  { id: 'Tree_N_Left', phase: 1.1 },
  { id: 'Tree_N_Center', phase: 2.2 },
  { id: 'Tree_N_Right', phase: 3.3 },
  { id: 'Tree_NE_Hero', phase: 4.4 },
  { id: 'Tree_W_Flank', phase: 5.1 },
  { id: 'Tree_E_Flank', phase: 5.9 },
];

/**
 * Configures a GLB-embedded material for either solid PBR rendering (trunks, boulders)
 * or crisp depth-writing alpha-cutout rendering (broadleaf & pine foliage, shrubs, ferns, grass, flowers).
 */
function configureGlbMaterial(
  rawMat: THREE.Material | THREE.Material[] | undefined,
  options: {
    isAlphaCutout?: boolean;
    alphaTest?: number;
    roughness?: number;
    metalness?: number;
    useVertexColors?: boolean;
  }
): THREE.MeshStandardMaterial {
  const baseMat = Array.isArray(rawMat) ? rawMat[0] : rawMat;
  const mat =
    baseMat && (baseMat as THREE.MeshStandardMaterial).isMeshStandardMaterial
      ? (baseMat as THREE.MeshStandardMaterial).clone()
      : new THREE.MeshStandardMaterial({ color: '#ffffff' });

  mat.roughness = options.roughness ?? 0.78;
  mat.metalness = options.metalness ?? 0.01;
  mat.depthWrite = true;
  mat.depthTest = true;

  if (options.useVertexColors !== undefined) {
    mat.vertexColors = options.useVertexColors;
  }

  if (mat.map) {
    mat.map.anisotropy = 8;
    mat.map.colorSpace = THREE.SRGBColorSpace;
  }
  if (mat.normalMap) {
    mat.normalMap.anisotropy = 4;
    mat.normalScale.set(0.85, 0.85);
  }

  if (options.isAlphaCutout) {
    mat.transparent = false;
    mat.alphaTest = options.alphaTest ?? 0.28;
    mat.side = THREE.DoubleSide;
  } else {
    mat.transparent = false;
    mat.alphaTest = 0.0;
    mat.side = THREE.FrontSide;
  }

  mat.needsUpdate = true;
  return mat;
}

export const TreesAndVegetation: React.FC<TreesAndVegetationProps> = ({ nodes, quality }) => {
  const canopyGroupRef = useRef<THREE.Group>(null);

  const getMeshAndMaterial = (
    name: string,
    opts: {
      isAlphaCutout?: boolean;
      alphaTest?: number;
      roughness?: number;
      metalness?: number;
      useVertexColors?: boolean;
    }
  ): { geometry: THREE.BufferGeometry; material: THREE.MeshStandardMaterial } | null => {
    const obj = nodes[name] as THREE.Mesh | undefined;
    if (!obj || !obj.isMesh || !obj.geometry) return null;
    const hasColorAttr = Boolean(obj.geometry.attributes.color);
    return {
      geometry: obj.geometry,
      material: configureGlbMaterial(obj.material, {
        ...opts,
        useVertexColors: opts.useVertexColors ?? hasColorAttr,
      }),
    };
  };

  const treeMeshes = useMemo(() => {
    return TREE_DEFS.map((t) => ({
      ...t,
      trunk: getMeshAndMaterial(`${t.id}_Trunk`, {
        isAlphaCutout: false,
        roughness: 0.84,
        metalness: 0.01,
      }),
      canopy: getMeshAndMaterial(`${t.id}_Canopy`, {
        isAlphaCutout: true,
        alphaTest: 0.28,
        roughness: 0.76,
        metalness: 0.01,
      }),
    }));
  }, [nodes]);

  const shrubsMesh = useMemo(
    () =>
      getMeshAndMaterial('Forest_Shrubs', {
        isAlphaCutout: true,
        alphaTest: 0.28,
        roughness: 0.76,
        metalness: 0.01,
      }),
    [nodes]
  );

  const rocksMesh = useMemo(
    () =>
      getMeshAndMaterial('Environment_Rocks', {
        isAlphaCutout: false,
        roughness: 0.82,
        metalness: 0.02,
        useVertexColors: false,
      }),
    [nodes]
  );

  const fernsMesh = useMemo(
    () =>
      getMeshAndMaterial('Forest_Ferns', {
        isAlphaCutout: true,
        alphaTest: 0.26,
        roughness: 0.72,
        metalness: 0.01,
        useVertexColors: false,
      }),
    [nodes]
  );

  const grassMesh = useMemo(
    () =>
      getMeshAndMaterial('Forest_Grass', {
        isAlphaCutout: true,
        alphaTest: 0.24,
        roughness: 0.74,
        metalness: 0.01,
        useVertexColors: false,
      }),
    [nodes]
  );

  const flowersMesh = useMemo(
    () =>
      getMeshAndMaterial('Wildflowers', {
        isAlphaCutout: true,
        alphaTest: 0.26,
        roughness: 0.58,
        metalness: 0.01,
        useVertexColors: false,
      }),
    [nodes]
  );

  useFrame(({ clock }) => {
    if (!quality.enableWindAnimation || !canopyGroupRef.current) return;
    const t = clock.getElapsedTime();
    canopyGroupRef.current.children.forEach((child, idx) => {
      const def = TREE_DEFS[idx];
      if (!def) return;
      child.rotation.z = Math.sin(t * 0.85 + def.phase) * 0.005;
      child.rotation.x = Math.cos(t * 0.68 + def.phase) * 0.004;
    });
  });

  return (
    <group name="TreesAndVegetationGroup">
      {/* Normal-Mapped Stylized Tree Trunks & Branch Skeletons (Quaternius CC0) */}
      {treeMeshes.map((t) => {
        if (!t.trunk) return null;
        return (
          <mesh
            key={`${t.id}_Trunk`}
            name={`${t.id}_Trunk`}
            geometry={t.trunk.geometry}
            material={t.trunk.material}
            castShadow={quality.shadows}
            receiveShadow={quality.shadows}
          />
        );
      })}

      {/* Alpha-Cutout Stylized Broadleaf & Evergreen Canopies (Quaternius CC0) */}
      <group ref={canopyGroupRef} name="TreeCanopies">
        {treeMeshes.map((t) => {
          if (!t.canopy) return null;
          return (
            <mesh
              key={`${t.id}_Canopy`}
              name={`${t.id}_Canopy`}
              geometry={t.canopy.geometry}
              material={t.canopy.material}
              castShadow={quality.shadows}
              receiveShadow={quality.shadows}
            />
          );
        })}
      </group>

      {/* Woodland Shrubs (Bush_Common & Bush_Common_Flowers) */}
      {shrubsMesh && (
        <mesh
          name="Forest_Shrubs"
          geometry={shrubsMesh.geometry}
          material={shrubsMesh.material}
          castShadow={quality.shadows}
          receiveShadow={quality.shadows}
        />
      )}

      {/* Hand-Painted Mossy Boulders & Creek Grotto Stones (Rock_Medium_1..3) */}
      {rocksMesh && (
        <mesh
          name="Environment_Rocks"
          geometry={rocksMesh.geometry}
          material={rocksMesh.material}
          castShadow={quality.shadows}
          receiveShadow={quality.shadows}
        />
      )}

      {/* Hand-Painted Woodland Ferns, Broadleaf Plants & Clovers */}
      {fernsMesh && (
        <mesh
          name="Forest_Ferns"
          geometry={fernsMesh.geometry}
          material={fernsMesh.material}
          castShadow={quality.shadows}
          receiveShadow={quality.shadows}
        />
      )}

      {/* Stylized Woodland Grass Tufts */}
      {grassMesh && (
        <mesh
          name="Forest_Grass"
          geometry={grassMesh.geometry}
          material={grassMesh.material}
          castShadow={false}
          receiveShadow={quality.shadows}
        />
      )}

      {/* Woodland Wildflower Blossoms & Flowering Shrub Petals */}
      {flowersMesh && (
        <mesh
          name="Wildflowers"
          geometry={flowersMesh.geometry}
          material={flowersMesh.material}
          castShadow={false}
          receiveShadow={quality.shadows}
        />
      )}
    </group>
  );
};
