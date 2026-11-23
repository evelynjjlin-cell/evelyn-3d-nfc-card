import React, { useMemo, useState } from 'react';
import { useFrame, ThreeEvent } from '@react-three/fiber';
import * as THREE from 'three';

interface IdentityPlaque3DProps {
  nodes: Record<string, THREE.Object3D>;
  shadows: boolean;
  onSelectPlaque?: () => void;
}

export const IdentityPlaque3D: React.FC<IdentityPlaque3DProps> = ({
  nodes,
  shadows,
  onSelectPlaque,
}) => {
  const [hovered, setHovered] = useState(false);

  const materials = useMemo(() => {
    return {
      brassFrame: new THREE.MeshStandardMaterial({
        color: '#E0CC9D',
        roughness: 0.28,
        metalness: 0.76,
      }),
      slatePlate: new THREE.MeshStandardMaterial({
        color: '#153329',
        roughness: 0.42,
        metalness: 0.22,
      }),
      nameRelief: new THREE.MeshStandardMaterial({
        color: '#FAF5E8',
        emissive: '#F2E3BE',
        emissiveIntensity: 0.22,
        roughness: 0.28,
        metalness: 0.12,
      }),
      titleRelief: new THREE.MeshStandardMaterial({
        color: '#E5D1A2',
        emissive: '#D8C08A',
        emissiveIntensity: 0.18,
        roughness: 0.3,
        metalness: 0.48,
      }),
    };
  }, []);

  useFrame((_, delta) => {
    materials.nameRelief.emissiveIntensity = THREE.MathUtils.lerp(
      materials.nameRelief.emissiveIntensity,
      hovered ? 0.48 : 0.22,
      delta * 8
    );
    materials.titleRelief.emissiveIntensity = THREE.MathUtils.lerp(
      materials.titleRelief.emissiveIntensity,
      hovered ? 0.42 : 0.18,
      delta * 8
    );
  });

  const getGeometry = (name: string): THREE.BufferGeometry | null => {
    const obj = nodes[name] as THREE.Mesh | undefined;
    return obj && obj.isMesh ? obj.geometry : null;
  };

  const frameGeo = getGeometry('Identity_Plaque_Frame');
  const plateGeo = getGeometry('Identity_Plaque_Plate');
  const nameGeo = getGeometry('Identity_Plaque_Name3D');
  const titleGeo = getGeometry('Identity_Plaque_Title3D');

  const handleClick = (e: ThreeEvent<MouseEvent>) => {
    e.stopPropagation();
    onSelectPlaque?.();
  };

  return (
    <group
      name="EmbeddedIdentityPlaque3D"
      onClick={handleClick}
      onPointerOver={(e) => {
        e.stopPropagation();
        setHovered(true);
        document.body.style.cursor = 'pointer';
      }}
      onPointerOut={() => {
        setHovered(false);
        document.body.style.cursor = 'auto';
      }}
    >
      {frameGeo && (
        <mesh
          name="Identity_Plaque_Frame"
          geometry={frameGeo}
          material={materials.brassFrame}
          castShadow={shadows}
          receiveShadow={shadows}
        />
      )}
      {plateGeo && (
        <mesh
          name="Identity_Plaque_Plate"
          geometry={plateGeo}
          material={materials.slatePlate}
          castShadow={shadows}
          receiveShadow={shadows}
        />
      )}
      {nameGeo && (
        <mesh
          name="Identity_Plaque_Name3D"
          geometry={nameGeo}
          material={materials.nameRelief}
          castShadow={shadows}
        />
      )}
      {titleGeo && (
        <mesh
          name="Identity_Plaque_Title3D"
          geometry={titleGeo}
          material={materials.titleRelief}
          castShadow={shadows}
        />
      )}
    </group>
  );
};
