import React, { useMemo, useRef, useState } from 'react';
import { useFrame, ThreeEvent } from '@react-three/fiber';
import * as THREE from 'three';
import { getMailboxPlaqueTexture, getWoodGrainTexture } from '../../utils/proceduralTextures';

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
  const plaqueTex = useMemo(() => getMailboxPlaqueTexture(), []);

  const materials = useMemo(() => {
    return {
      post: new THREE.MeshStandardMaterial({
        color: '#7A5030',
        roughness: 0.7,
        metalness: 0.04,
        bumpMap: woodBump,
        bumpScale: 0.016,
      }),
      body: new THREE.MeshStandardMaterial({
        color: '#1E493B',
        roughness: 0.36,
        metalness: 0.28,
      }),
      brass: new THREE.MeshStandardMaterial({
        color: '#E2CE9F',
        roughness: 0.28,
        metalness: 0.68,
      }),
      letter: new THREE.MeshStandardMaterial({
        color: '#FAF6EC',
        emissive: '#F4E5C2',
        emissiveIntensity: 0.25,
        roughness: 0.35,
      }),
      waxSeal: new THREE.MeshStandardMaterial({
        color: '#9E332E',
        roughness: 0.35,
        metalness: 0.15,
      }),
    };
  }, [woodBump]);

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
      isActive ? 0.6 : 0.0,
      delta * 8
    );
    materials.brass.emissive.set(isActive ? '#8C7345' : '#000000');
    materials.brass.emissiveIntensity = THREE.MathUtils.lerp(
      materials.brass.emissiveIntensity,
      isActive ? 0.45 : 0.0,
      delta * 8
    );

    if (groupRef.current) {
      groupRef.current.position.y = THREE.MathUtils.lerp(
        groupRef.current.position.y,
        isActive ? 0.035 : 0.0,
        delta * 9
      );
    }

    // Animate door & emerging letter when mailbox is opened or hovered
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

      {/* Emerging folded contact letter with wax seal */}
      <group ref={letterGroupRef} name="EmergingContactLetter">
        {letterGeo && (
          <mesh
            geometry={letterGeo}
            material={materials.letter}
            castShadow={shadows}
          />
        )}
        {/* Wax seal emblem on the emerging letter */}
        <mesh position={[0.84, 1.32, 1.48]} rotation={[0.25, -0.28, 0]}>
          <cylinderGeometry args={[0.036, 0.036, 0.015, 16]} />
          <primitive object={materials.waxSeal} attach="material" />
        </mesh>
      </group>

      {/* Diegetic "CONTACT" brass-and-forest nameplate mounted on the mailbox post */}
      <group
        position={[0.83, 0.72, 1.42]}
        rotation={[-0.08, THREE.MathUtils.degToRad(-16), 0]}
      >
        <mesh castShadow={shadows}>
          <boxGeometry args={[0.64, 0.24, 0.035]} />
          <meshStandardMaterial color="#5A3820" roughness={0.55} />
        </mesh>
        <mesh position={[0, 0, 0.02]}>
          <planeGeometry args={[0.6, 0.21]} />
          <meshStandardMaterial
            map={plaqueTex}
            roughness={0.38}
            emissive="#DCC99D"
            emissiveIntensity={hovered || isOpen ? 0.22 : 0.06}
          />
        </mesh>
      </group>

      {/* Subtle ground glow ring when hovered or opened */}
      {(hovered || activeHover === 'mailbox' || isOpen) && (
        <mesh position={[0.9, 0.16, 1.2]} rotation={[-Math.PI / 2, 0, 0]}>
          <ringGeometry args={[0.28, 0.42, 32]} />
          <meshBasicMaterial color="#DCC99D" transparent opacity={0.7} side={THREE.DoubleSide} />
        </mesh>
      )}

      {/* Generous invisible click/tap hitbox for smartphone touch */}
      <mesh
        name="Hitbox_Mailbox"
        position={[0.88, 0.92, 1.24]}
        rotation={[0, THREE.MathUtils.degToRad(-16), 0]}
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
