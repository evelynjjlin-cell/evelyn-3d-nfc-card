import React, { useMemo, useRef, useState } from 'react';
import { useFrame, ThreeEvent } from '@react-three/fiber';
import * as THREE from 'three';
import {
  getWoodGrainAlbedoTexture,
  getWoodGrainTexture,
  getWoodRoughnessTexture,
} from '../../utils/proceduralTextures';

export type SignId = 'ux' | 'game';

interface WoodenSignsProps {
  nodes: Record<string, THREE.Object3D>;
  shadows: boolean;
  activeHover: string | null;
  onHoverChange: (id: string | null) => void;
  onSelectSign: (id: SignId) => void;
}

export const WoodenSigns: React.FC<WoodenSignsProps> = ({
  nodes,
  shadows,
  activeHover,
  onHoverChange,
  onSelectSign,
}) => {
  const uxGroupRef = useRef<THREE.Group>(null);
  const gameGroupRef = useRef<THREE.Group>(null);
  const pointerDownPos = useRef<{ x: number; y: number } | null>(null);

  const [uxHovered, setUxHovered] = useState(false);
  const [gameHovered, setGameHovered] = useState(false);

  const woodBump = useMemo(() => getWoodGrainTexture(), []);
  const woodAlbedo = useMemo(() => getWoodGrainAlbedoTexture(), []);
  const woodRoughness = useMemo(() => getWoodRoughnessTexture(), []);

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
      uxBoard: new THREE.MeshStandardMaterial({
        color: '#ffffff',
        vertexColors: true,
        map: woodAlbedo,
        roughnessMap: woodRoughness,
        roughness: 0.76,
        metalness: 0.02,
        bumpMap: woodBump,
        bumpScale: 0.020,
        transparent: false,
        opacity: 1.0,
        depthWrite: true,
        depthTest: true,
        side: THREE.FrontSide,
      }),
      gameBoard: new THREE.MeshStandardMaterial({
        color: '#ffffff',
        vertexColors: true,
        map: woodAlbedo,
        roughnessMap: woodRoughness,
        roughness: 0.76,
        metalness: 0.02,
        bumpMap: woodBump,
        bumpScale: 0.020,
        transparent: false,
        opacity: 1.0,
        depthWrite: true,
        depthTest: true,
        side: THREE.FrontSide,
      }),
      uxLettering: new THREE.MeshStandardMaterial({
        color: '#F7F1E4',
        emissive: '#EAD8B1',
        emissiveIntensity: 0.14,
        roughness: 0.36,
        metalness: 0.04,
        transparent: false,
        depthWrite: true,
        depthTest: true,
        side: THREE.FrontSide,
      }),
      gameLettering: new THREE.MeshStandardMaterial({
        color: '#F7F1E4',
        emissive: '#EAD8B1',
        emissiveIntensity: 0.14,
        roughness: 0.36,
        metalness: 0.04,
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

  useFrame((_, delta) => {
    const isUxActive = uxHovered || activeHover === 'ux';
    const isGameActive = gameHovered || activeHover === 'game';

    materials.uxBoard.emissive.set(isUxActive ? '#4A2E14' : '#000000');
    materials.uxBoard.emissiveIntensity = THREE.MathUtils.lerp(
      materials.uxBoard.emissiveIntensity,
      isUxActive ? 0.38 : 0.0,
      delta * 8
    );
    materials.uxLettering.emissiveIntensity = THREE.MathUtils.lerp(
      materials.uxLettering.emissiveIntensity,
      isUxActive ? 0.54 : 0.14,
      delta * 8
    );

    materials.gameBoard.emissive.set(isGameActive ? '#4A2E14' : '#000000');
    materials.gameBoard.emissiveIntensity = THREE.MathUtils.lerp(
      materials.gameBoard.emissiveIntensity,
      isGameActive ? 0.38 : 0.0,
      delta * 8
    );
    materials.gameLettering.emissiveIntensity = THREE.MathUtils.lerp(
      materials.gameLettering.emissiveIntensity,
      isGameActive ? 0.54 : 0.14,
      delta * 8
    );

    if (uxGroupRef.current) {
      uxGroupRef.current.position.y = THREE.MathUtils.lerp(
        uxGroupRef.current.position.y,
        isUxActive ? 0.032 : 0.0,
        delta * 9
      );
    }
    if (gameGroupRef.current) {
      gameGroupRef.current.position.y = THREE.MathUtils.lerp(
        gameGroupRef.current.position.y,
        isGameActive ? 0.032 : 0.0,
        delta * 9
      );
    }
  });

  const handlePointerDown = (e: ThreeEvent<PointerEvent>) => {
    pointerDownPos.current = { x: e.clientX, y: e.clientY };
  };

  const handleSignClick = (e: ThreeEvent<MouseEvent>, id: SignId) => {
    e.stopPropagation();
    if (pointerDownPos.current) {
      const dist = Math.hypot(
        e.clientX - pointerDownPos.current.x,
        e.clientY - pointerDownPos.current.y
      );
      if (dist > 10) return;
    }
    onSelectSign(id);
  };

  const uxPostGeo = getGeometry('Signpost_UX_Post');
  const uxBoardGeo = getGeometry('Signpost_UX_Board');
  const uxLabelGeo = getGeometry('Signpost_UX_Label3D');

  const gamePostGeo = getGeometry('Signpost_Game_Post');
  const gameBoardGeo = getGeometry('Signpost_Game_Board');
  const gameLabelGeo = getGeometry('Signpost_Game_Label3D');

  return (
    <group name="InteractiveWoodenSigns">
      {/* 1. DESIGN TRAIL SIGNPOST (Left Crossroads Trail -> https://evelynjlin.com) */}
      <group ref={uxGroupRef} name="Signpost_UX_Interactive">
        {uxPostGeo && (
          <mesh
            geometry={uxPostGeo}
            material={materials.post}
            castShadow={shadows}
            receiveShadow={shadows}
          />
        )}
        {uxBoardGeo && (
          <mesh
            geometry={uxBoardGeo}
            material={materials.uxBoard}
            castShadow={shadows}
            receiveShadow={shadows}
          />
        )}
        {uxLabelGeo && (
          <mesh
            geometry={uxLabelGeo}
            material={materials.uxLettering}
            castShadow={shadows}
          />
        )}

        {(uxHovered || activeHover === 'ux') && (
          <mesh position={[-1.58, 0.28, -0.68]} rotation={[-Math.PI / 2, 0, 0]}>
            <ringGeometry args={[0.3, 0.43, 32]} />
            <meshBasicMaterial color="#DCC99D" transparent opacity={0.62} side={THREE.DoubleSide} />
          </mesh>
        )}

        <mesh
          name="Hitbox_Sign_UX"
          position={[-1.58, 1.3, -0.62]}
          rotation={[0, THREE.MathUtils.degToRad(18), 0]}
          onPointerDown={handlePointerDown}
          onClick={(e) => handleSignClick(e, 'ux')}
          onPointerOver={(e) => {
            e.stopPropagation();
            setUxHovered(true);
            onHoverChange('ux');
            document.body.style.cursor = 'pointer';
          }}
          onPointerOut={() => {
            setUxHovered(false);
            onHoverChange(null);
            document.body.style.cursor = 'auto';
          }}
        >
          <boxGeometry args={[1.95, 0.92, 0.55]} />
          <meshBasicMaterial transparent opacity={0} depthWrite={false} />
        </mesh>
      </group>

      {/* 2. GAME TRAIL SIGNPOST (Right Crossroads Trail -> Game Worlds) */}
      <group ref={gameGroupRef} name="Signpost_Game_Interactive">
        {gamePostGeo && (
          <mesh
            geometry={gamePostGeo}
            material={materials.post}
            castShadow={shadows}
            receiveShadow={shadows}
          />
        )}
        {gameBoardGeo && (
          <mesh
            geometry={gameBoardGeo}
            material={materials.gameBoard}
            castShadow={shadows}
            receiveShadow={shadows}
          />
        )}
        {gameLabelGeo && (
          <mesh
            geometry={gameLabelGeo}
            material={materials.gameLettering}
            castShadow={shadows}
          />
        )}

        {(gameHovered || activeHover === 'game') && (
          <mesh position={[1.58, 0.27, -0.64]} rotation={[-Math.PI / 2, 0, 0]}>
            <ringGeometry args={[0.3, 0.43, 32]} />
            <meshBasicMaterial color="#DCC99D" transparent opacity={0.62} side={THREE.DoubleSide} />
          </mesh>
        )}

        <mesh
          name="Hitbox_Sign_Game"
          position={[1.58, 1.28, -0.58]}
          rotation={[0, THREE.MathUtils.degToRad(-18), 0]}
          onPointerDown={handlePointerDown}
          onClick={(e) => handleSignClick(e, 'game')}
          onPointerOver={(e) => {
            e.stopPropagation();
            setGameHovered(true);
            onHoverChange('game');
            document.body.style.cursor = 'pointer';
          }}
          onPointerOut={() => {
            setGameHovered(false);
            onHoverChange(null);
            document.body.style.cursor = 'auto';
          }}
        >
          <boxGeometry args={[1.95, 0.92, 0.55]} />
          <meshBasicMaterial transparent opacity={0} depthWrite={false} />
        </mesh>
      </group>
    </group>
  );
};
