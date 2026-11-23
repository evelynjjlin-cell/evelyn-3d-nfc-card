import React, { useMemo, useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { QualityPreset } from '../../config/personalConfig';
import { getWoodGrainTexture } from '../../utils/proceduralTextures';

interface TreesAndVegetationProps {
  nodes: Record<string, THREE.Object3D>;
  quality: QualityPreset;
}

const TREE_DEFS = [
  { id: 'Tree_NW_Hero', variant: 0, phase: 0.0 },
  { id: 'Tree_N_Left', variant: 1, phase: 1.1 },
  { id: 'Tree_N_Center', variant: 0, phase: 2.2 },
  { id: 'Tree_N_Right', variant: 2, phase: 3.3 },
  { id: 'Tree_NE_Hero', variant: 1, phase: 4.4 },
  { id: 'Tree_W_Flank', variant: 2, phase: 5.1 },
  { id: 'Tree_E_Flank', variant: 0, phase: 5.9 },
];

export const TreesAndVegetation: React.FC<TreesAndVegetationProps> = ({ nodes, quality }) => {
  const canopyGroupRef = useRef<THREE.Group>(null);
  const woodBump = useMemo(() => getWoodGrainTexture(), []);

  const materials = useMemo(() => {
    return {
      bark: new THREE.MeshStandardMaterial({
        color: '#6E4E37',
        roughness: 0.82,
        metalness: 0.02,
        bumpMap: woodBump,
        bumpScale: 0.018,
      }),
      foliage: [
        new THREE.MeshStandardMaterial({
          color: '#214E3E',
          roughness: 0.72,
          metalness: 0.02,
        }),
        new THREE.MeshStandardMaterial({
          color: '#4F704B',
          roughness: 0.74,
          metalness: 0.02,
        }),
        new THREE.MeshStandardMaterial({
          color: '#769273',
          roughness: 0.75,
          metalness: 0.02,
        }),
      ],
      rocks: new THREE.MeshStandardMaterial({
        color: '#6E7868',
        roughness: 0.78,
        metalness: 0.04,
      }),
      ferns: new THREE.MeshStandardMaterial({
        color: '#4A6E46',
        roughness: 0.68,
        metalness: 0.02,
        side: THREE.DoubleSide,
      }),
      wildflowers: new THREE.MeshStandardMaterial({
        color: '#F6F1E4',
        emissive: '#DCC99D',
        emissiveIntensity: 0.22,
        roughness: 0.4,
      }),
    };
  }, [woodBump]);

  const getGeometry = (name: string): THREE.BufferGeometry | null => {
    const obj = nodes[name] as THREE.Mesh | undefined;
    return obj && obj.isMesh ? obj.geometry : null;
  };

  useFrame(({ clock }) => {
    if (!quality.enableWindAnimation || !canopyGroupRef.current) return;
    const t = clock.getElapsedTime();
    canopyGroupRef.current.children.forEach((child, idx) => {
      const def = TREE_DEFS[idx];
      if (!def) return;
      child.rotation.z = Math.sin(t * 0.95 + def.phase) * 0.008;
      child.rotation.x = Math.cos(t * 0.75 + def.phase) * 0.006;
    });
  });

  const rocksGeo = getGeometry('Environment_Rocks');
  const fernsGeo = getGeometry('Forest_Ferns');
  const flowersGeo = getGeometry('Wildflowers');

  return (
    <group name="TreesAndVegetationGroup">
      {/* Tree Trunks */}
      {TREE_DEFS.map((t) => {
        const trunkGeo = getGeometry(`${t.id}_Trunk`);
        if (!trunkGeo) return null;
        return (
          <mesh
            key={`${t.id}_Trunk`}
            name={`${t.id}_Trunk`}
            geometry={trunkGeo}
            material={materials.bark}
            castShadow={quality.shadows}
            receiveShadow={quality.shadows}
          />
        );
      })}

      {/* Sculpted Tree Canopies with subtle wind breathing */}
      <group ref={canopyGroupRef} name="TreeCanopies">
        {TREE_DEFS.map((t) => {
          const canopyGeo = getGeometry(`${t.id}_Canopy`);
          if (!canopyGeo) return null;
          return (
            <mesh
              key={`${t.id}_Canopy`}
              name={`${t.id}_Canopy`}
              geometry={canopyGeo}
              material={materials.foliage[t.variant % 3]}
              castShadow={quality.shadows}
              receiveShadow={quality.shadows}
            />
          );
        })}
      </group>

      {/* Mossy Boulders */}
      {rocksGeo && (
        <mesh
          name="Environment_Rocks"
          geometry={rocksGeo}
          material={materials.rocks}
          castShadow={quality.shadows}
          receiveShadow={quality.shadows}
        />
      )}

      {/* Botanical Fern Rosettes */}
      {fernsGeo && (
        <mesh
          name="Forest_Ferns"
          geometry={fernsGeo}
          material={materials.ferns}
          castShadow={quality.shadows}
          receiveShadow={quality.shadows}
        />
      )}

      {/* Wildflower Blossoms */}
      {flowersGeo && (
        <mesh
          name="Wildflowers"
          geometry={flowersGeo}
          material={materials.wildflowers}
          castShadow={false}
        />
      )}
    </group>
  );
};
