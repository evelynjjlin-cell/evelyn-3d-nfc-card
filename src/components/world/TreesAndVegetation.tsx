import React, { useMemo, useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { QualityPreset } from '../../config/personalConfig';
import {
  getFoliageBumpTexture,
  getGrassBumpTexture,
  getWoodGrainTexture,
} from '../../utils/proceduralTextures';

interface TreesAndVegetationProps {
  nodes: Record<string, THREE.Object3D>;
  quality: QualityPreset;
}

const TREE_DEFS = [
  { id: 'Tree_NW_Hero', variant: 0, phase: 0.0 },
  { id: 'Tree_N_Left', variant: 2, phase: 1.1 },
  { id: 'Tree_N_Center', variant: 1, phase: 2.2 },
  { id: 'Tree_N_Right', variant: 2, phase: 3.3 },
  { id: 'Tree_NE_Hero', variant: 1, phase: 4.4 },
  { id: 'Tree_W_Flank', variant: 1, phase: 5.1 },
  { id: 'Tree_E_Flank', variant: 0, phase: 5.9 },
];

export const TreesAndVegetation: React.FC<TreesAndVegetationProps> = ({ nodes, quality }) => {
  const canopyGroupRef = useRef<THREE.Group>(null);
  const woodBump = useMemo(() => getWoodGrainTexture(), []);
  const foliageBump = useMemo(() => getFoliageBumpTexture(), []);
  const rockBump = useMemo(() => getGrassBumpTexture(), []);

  const materials = useMemo(() => {
    return {
      bark: new THREE.MeshStandardMaterial({
        color: '#ffffff',
        vertexColors: true,
        roughness: 0.84,
        metalness: 0.02,
        bumpMap: woodBump,
        bumpScale: 0.022,
      }),
      foliage: new THREE.MeshStandardMaterial({
        color: '#ffffff',
        vertexColors: true,
        roughness: 0.72,
        metalness: 0.01,
        bumpMap: foliageBump,
        bumpScale: 0.024,
      }),
      rocks: new THREE.MeshStandardMaterial({
        color: '#ffffff',
        vertexColors: true,
        roughness: 0.8,
        metalness: 0.03,
        bumpMap: rockBump,
        bumpScale: 0.022,
      }),
      fernsAndGrass: new THREE.MeshStandardMaterial({
        color: '#ffffff',
        vertexColors: true,
        roughness: 0.68,
        metalness: 0.01,
        bumpMap: foliageBump,
        bumpScale: 0.012,
        side: THREE.DoubleSide,
      }),
      wildflowers: new THREE.MeshStandardMaterial({
        color: '#F6F1E4',
        emissive: '#DCC99D',
        emissiveIntensity: 0.16,
        roughness: 0.42,
      }),
    };
  }, [woodBump, foliageBump, rockBump]);

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
      child.rotation.z = Math.sin(t * 0.9 + def.phase) * 0.007;
      child.rotation.x = Math.cos(t * 0.72 + def.phase) * 0.005;
    });
  });

  const rocksGeo = getGeometry('Environment_Rocks');
  const fernsGeo = getGeometry('Forest_Ferns');
  const flowersGeo = getGeometry('Wildflowers');

  return (
    <group name="TreesAndVegetationGroup">
      {/* Sculpted Tree Trunks & Visible Secondary Branches */}
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

      {/* Sculpted Multi-Cluster Tree Canopies with 3D Vertex Color Sun/AO Gradients */}
      <group ref={canopyGroupRef} name="TreeCanopies">
        {TREE_DEFS.map((t) => {
          const canopyGeo = getGeometry(`${t.id}_Canopy`);
          if (!canopyGeo) return null;
          return (
            <mesh
              key={`${t.id}_Canopy`}
              name={`${t.id}_Canopy`}
              geometry={canopyGeo}
              material={materials.foliage}
              castShadow={quality.shadows}
              receiveShadow={quality.shadows}
            />
          );
        })}
      </group>

      {/* Chiseled Mossy Boulders & Creek Stones */}
      {rocksGeo && (
        <mesh
          name="Environment_Rocks"
          geometry={rocksGeo}
          material={materials.rocks}
          castShadow={quality.shadows}
          receiveShadow={quality.shadows}
        />
      )}

      {/* Botanical Ferns & 3D Multi-Blade Grass Clumps */}
      {fernsGeo && (
        <mesh
          name="Forest_Ferns"
          geometry={fernsGeo}
          material={materials.fernsAndGrass}
          castShadow={quality.shadows}
          receiveShadow={quality.shadows}
        />
      )}

      {/* Multi-Petal Wildflower Clusters */}
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
