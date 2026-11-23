import React, { useMemo, useRef, useState } from 'react';
import { useFrame, ThreeEvent } from '@react-three/fiber';
import * as THREE from 'three';
import {
  getMailboxPlaqueTexture,
  getWoodGrainAlbedoTexture,
  getWoodGrainTexture,
  getWoodRoughnessTexture,
} from '../../utils/proceduralTextures';

interface MailboxProps {
  nodes: Record<string, THREE.Object3D>;
  shadows: boolean;
  isOpen: boolean;
  activeHover: string | null;
  onHoverChange: (id: string | null) => void;
  onSelectMailbox: () => void;
}

export const Mailbox: React.FC<MailboxProps> = ({
  nodes,
  shadows,
  isOpen,
  activeHover,
  onHoverChange,
  onSelectMailbox,
}) => {
  const groupRef = useRef<THREE.Group>(null);
  const doorRef = useRef<THREE.Mesh>(null);
  const letterGroupRef = useRef<THREE.Group>(null);
  const pointerDownPos = useRef<{ x: number; y: number } | null>(null);
  const [hovered, setHovered] = useState(false);

  const woodBump = useMemo(() => getWoodGrainTexture(), []);
  const woodAlbedo = useMemo(() => getWoodGrainAlbedoTexture(), []);
  const woodRoughness = useMemo(() => getWoodRoughnessTexture(), []);
  const plaqueTex = useMemo(() => getMailboxPlaqueTexture(), []);

  const materials = useMemo(() => {
    return {
      post: new THREE.MeshStandardMaterial({
        color: '#ffffff',
        vertexColors: true,
        map: woodAlbedo,
        roughnessMap: woodRoughness,
        roughness: 0.80,
        metalness: 0.02,
        bumpMap: woodBump,
        bumpScale: 0.024,
        transparent: false,
        opacity: 1.0,
        depthWrite: true,
        depthTest: true,
        side: THREE.FrontSide,
      }),
      body: new THREE.MeshStandardMaterial({
        color: '#1E4A3B',
        roughness: 0.42,
        metalness: 0.24,
        transparent: false,
        opacity: 1.0,
        depthWrite: true,
        depthTest: true,
        side: THREE.FrontSide,
      }),
      brass: new THREE.MeshStandardMaterial({
        color: '#E0CB9B',
        roughness: 0.32,
        metalness: 0.68,
        transparent: false,
        opacity: 1.0,
        depthWrite: true,
        depthTest: true,
        side: THREE.FrontSide,
      }),
      letter: new THREE.MeshStandardMaterial({
        color: '#FAF5E8',
        emissive: '#F2E2BD',
        emissiveIntensity: 0.16,
        roughness: 0.38,
        transparent: false,
        depthWrite: true,
        depthTest: true,
        side: THREE.FrontSide,
      }),
      waxSeal: new THREE.MeshStandardMaterial({
        color: '#9C322D',
        roughness: 0.34,
        metalness: 0.15,
        transparent: false,
        depthWrite: true,
        depthTest: true,
        side: THREE.FrontSide,
      }),
    };
  }, [woodAlbedo, woodBump, woodRoughness]);

  const getGeometry = (name: string): THREE.BufferGeometry | null => {
    const obj = nodes[name] as THREE.Mesh | undefined;
    return obj && obj.isMesh ? obj.geometry : null;
  };

  useFrame(({ clock }, delta) => {
    const isActive = hovered || activeHover === 'mailbox' || isOpen;
    const t = clock.getElapsedTime();

    materials.body.emissive.set(isActive ? '#173A2E' : '#000000');
    materials.body.emissiveIntensity = THREE.MathUtils.lerp(
      materials.body.emissiveIntensity,
      isActive ? 0.45 : 0.0,
      delta * 8
    );
    materials.brass.emissive.set(isActive ? '#8C7345' : '#000000');
    materials.brass.emissiveIntensity = THREE.MathUtils.lerp(
      materials.brass.emissiveIntensity,
      isActive ? 0.38 : 0.0,
      delta * 8
    );

    if (groupRef.current) {
      groupRef.current.position.y = THREE.MathUtils.lerp(
        groupRef.current.position.y,
        isActive ? 0.032 : 0.0,
        delta * 9
      );
    }

    if (doorRef.current) {
      const targetOffsetY = isOpen ? -0.05 : hovered ? -0.015 : 0.0;
      const targetOffsetZ = isOpen ? 0.06 : hovered ? 0.02 : 0.0;
      doorRef.current.position.y = THREE.MathUtils.lerp(
        doorRef.current.position.y,
        targetOffsetY,
        delta * 8
      );
      doorRef.current.position.z = THREE.MathUtils.lerp(
        doorRef.current.position.z,
        targetOffsetZ,
        delta * 8
      );
    }

    if (letterGroupRef.current) {
      const targetZ = isOpen ? 0.18 : hovered ? 0.06 : 0.0;
      const targetY = isOpen ? 0.09 + Math.sin(t * 2.5) * 0.015 : hovered ? 0.03 : 0.0;
      letterGroupRef.current.position.z = THREE.MathUtils.lerp(
        letterGroupRef.current.position.z,
        targetZ,
        delta * 7
      );
      letterGroupRef.current.position.y = THREE.MathUtils.lerp(
        letterGroupRef.current.position.y,
        targetY,
        delta * 7
      );
    }
  });

  const handlePointerDown = (e: ThreeEvent<PointerEvent>) => {
    pointerDownPos.current = { x: e.clientX, y: e.clientY };
  };

  const handleClick = (e: ThreeEvent<MouseEvent>) => {
    e.stopPropagation();
    if (pointerDownPos.current) {
      const dist = Math.hypot(
        e.clientX - pointerDownPos.current.x,
        e.clientY - pointerDownPos.current.y
      );
      if (dist > 10) return;
    }
    onSelectMailbox();
  };

  const postGeo = getGeometry('Mailbox_Post');
  const bodyGeo = getGeometry('Mailbox_Body');
  const doorGeo = getGeometry('Mailbox_Door');
  const letterGeo = getGeometry('Mailbox_Letter');
  const flagGeo = getGeometry('Mailbox_Flag');

  return (
    <group ref={groupRef} name="WoodlandMailboxInteractive">
      {postGeo && (
        <mesh
          geometry={postGeo}
          material={materials.post}
          castShadow={shadows}
          receiveShadow={shadows}
        />
      )}
      {bodyGeo && (
        <mesh
          geometry={bodyGeo}
          material={materials.body}
          castShadow={shadows}
          receiveShadow={shadows}
        />
      )}
      {doorGeo && (
        <mesh
          ref={doorRef}
          geometry={doorGeo}
          material={materials.brass}
          castShadow={shadows}
        />
      )}
      {flagGeo && (
        <mesh
          geometry={flagGeo}
          material={materials.brass}
          castShadow={shadows}
        />
      )}

      {/* Emerging folded contact letter with crimson wax seal */}
      <group ref={letterGroupRef} name="EmergingContactLetter">
        {letterGeo && (
          <mesh
            geometry={letterGeo}
            material={materials.letter}
            castShadow={shadows}
          />
        )}
        <mesh position={[1.18, 1.35, 1.54]} rotation={[0.25, -0.38, 0]}>
          <cylinderGeometry args={[0.034, 0.034, 0.015, 16]} />
          <primitive object={materials.waxSeal} attach="material" />
        </mesh>
      </group>

      {/* Compact engraved brass nameplate mounted cleanly on the vertical oak post below the corbel brace */}
      <group
        position={[1.23, 0.62, 1.47]}
        rotation={[0.0, THREE.MathUtils.degToRad(-22), 0]}
      >
        <mesh castShadow={shadows}>
          <boxGeometry args={[0.38, 0.11, 0.026]} />
          <meshStandardMaterial
            color="#583820"
            roughness={0.76}
            metalness={0.02}
            transparent={false}
            depthWrite={true}
            depthTest={true}
          />
        </mesh>
        <mesh position={[0, 0, 0.014]}>
          <planeGeometry args={[0.35, 0.092]} />
          <meshStandardMaterial
            map={plaqueTex}
            roughness={0.38}
            emissive="#DCC99D"
            emissiveIntensity={hovered || isOpen ? 0.22 : 0.05}
            transparent={false}
            depthWrite={true}
            depthTest={true}
          />
        </mesh>
      </group>

      {(hovered || activeHover === 'mailbox' || isOpen) && (
        <mesh position={[1.28, 0.21, 1.36]} rotation={[-Math.PI / 2, 0, 0]}>
          <ringGeometry args={[0.26, 0.39, 32]} />
          <meshBasicMaterial color="#DCC99D" transparent opacity={0.68} side={THREE.DoubleSide} />
        </mesh>
      )}

      <mesh
        name="Hitbox_Mailbox"
        position={[1.28, 0.96, 1.38]}
        rotation={[0, THREE.MathUtils.degToRad(-22), 0]}
        onPointerDown={handlePointerDown}
        onClick={handleClick}
        onPointerOver={(e) => {
          e.stopPropagation();
          setHovered(true);
          onHoverChange('mailbox');
          document.body.style.cursor = 'pointer';
        }}
        onPointerOut={() => {
          setHovered(false);
          onHoverChange(null);
          document.body.style.cursor = 'auto';
        }}
      >
        <boxGeometry args={[0.96, 1.35, 0.98]} />
        <meshBasicMaterial transparent opacity={0} depthWrite={false} />
      </mesh>
    </group>
  );
};
