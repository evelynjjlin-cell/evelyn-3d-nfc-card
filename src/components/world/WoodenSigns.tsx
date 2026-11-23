import React, { useMemo, useRef, useState } from 'react';
import { useFrame, ThreeEvent } from '@react-three/fiber';
import * as THREE from 'three';
import { PERSONAL_CONFIG } from '../../config/personalConfig';
import { getSignPlaqueTexture, getWoodGrainTexture } from '../../utils/proceduralTextures';

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
  const uxPlaqueTex = useMemo(
    () => getSignPlaqueTexture(PERSONAL_CONFIG.destinations.uxPortfolioLabel, 'left'),
    []
  );
  const gamePlaqueTex = useMemo(
    () => getSignPlaqueTexture(PERSONAL_CONFIG.destinations.gamePortfolioLabel, 'right'),
    []
  );

  const materials = useMemo(() => {
    return {
      post: new THREE.MeshStandardMaterial({
        color: '#ffffff',
        vertexColors: true,
        roughness: 0.72,
        metalness: 0.04,
        bumpMap: woodBump,
        bumpScale: 0.018,
      }),
      uxBoard: new THREE.MeshStandardMaterial({
        color: '#ffffff',
        vertexColors: true,
        roughness: 0.62,
        metalness: 0.04,
        bumpMap: woodBump,
        bumpScale: 0.016,
      }),
      gameBoard: new THREE.MeshStandardMaterial({
        color: '#ffffff',
        vertexColors: true,
        roughness: 0.62,
        metalness: 0.04,
        bumpMap: woodBump,
        bumpScale: 0.016,
      }),
      uxLettering: new THREE.MeshStandardMaterial({
        color: '#F5EFE2',
        emissive: '#EAD8B1',
        emissiveIntensity: 0.16,
        roughness: 0.36,
      }),
      gameLettering: new THREE.MeshStandardMaterial({
        color: '#F5EFE2',
        emissive: '#EAD8B1',
        emissiveIntensity: 0.16,
        roughness: 0.36,
      }),
    };
  }, [woodBump]);

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
      isUxActive ? 0.45 : 0.0,
      delta * 8
    );
    materials.uxLettering.emissiveIntensity = THREE.MathUtils.lerp(
      materials.uxLettering.emissiveIntensity,
      isUxActive ? 0.62 : 0.16,
      delta * 8
    );

    materials.gameBoard.emissive.set(isGameActive ? '#4A2E14' : '#000000');
    materials.gameBoard.emissiveIntensity = THREE.MathUtils.lerp(
      materials.gameBoard.emissiveIntensity,
      isGameActive ? 0.45 : 0.0,
      delta * 8
    );
    materials.gameLettering.emissiveIntensity = THREE.MathUtils.lerp(
      materials.gameLettering.emissiveIntensity,
      isGameActive ? 0.62 : 0.16,
      delta * 8
    );

    if (uxGroupRef.current) {
      uxGroupRef.current.position.y = THREE.MathUtils.lerp(
        uxGroupRef.current.position.y,
        isUxActive ? 0.035 : 0.0,
        delta * 9
      );
    }
    if (gameGroupRef.current) {
      gameGroupRef.current.position.y = THREE.MathUtils.lerp(
        gameGroupRef.current.position.y,
        isGameActive ? 0.035 : 0.0,
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
      {/* 1. UX PORTFOLIO SIGNPOST (Left Crossroads Branch) */}
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

        {/* Flush back-side plaque so label stays readable if orbited from behind */}
        <mesh
          position={[-1.58, 1.42, -0.62]}
          rotation={[0, Math.PI + THREE.MathUtils.degToRad(18), 0]}
        >
          <planeGeometry args={[1.38, 0.38]} />
          <meshStandardMaterial map={uxPlaqueTex} roughness={0.55} />
        </mesh>

        {(uxHovered || activeHover === 'ux') && (
          <mesh position={[-1.58, 0.28, -0.62]} rotation={[-Math.PI / 2, 0, 0]}>
            <ringGeometry args={[0.3, 0.43, 32]} />
            <meshBasicMaterial color="#DCC99D" transparent opacity={0.62} side={THREE.DoubleSide} />
          </mesh>
        )}

        <mesh
          name="Hitbox_Sign_UX"
          position={[-1.58, 1.3, -0.56]}
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

      {/* 2. GAME PORTFOLIO SIGNPOST (Right Crossroads Branch) */}
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

        <mesh
          position={[1.58, 1.4, -0.58]}
          rotation={[0, Math.PI - THREE.MathUtils.degToRad(18), 0]}
        >
          <planeGeometry args={[1.38, 0.38]} />
          <meshStandardMaterial map={gamePlaqueTex} roughness={0.55} />
        </mesh>

        {(gameHovered || activeHover === 'game') && (
          <mesh position={[1.58, 0.27, -0.58]} rotation={[-Math.PI / 2, 0, 0]}>
            <ringGeometry args={[0.3, 0.43, 32]} />
            <meshBasicMaterial color="#DCC99D" transparent opacity={0.62} side={THREE.DoubleSide} />
          </mesh>
        )}

        <mesh
          name="Hitbox_Sign_Game"
          position={[1.58, 1.28, -0.52]}
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
