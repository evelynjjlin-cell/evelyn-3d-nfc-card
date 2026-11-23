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
    () => getSignPlaqueTexture(PERSONAL_CONFIG.destinations.uxPortfolioLabel, 'left', 'evelynjlin.com'),
    []
  );
  const gamePlaqueTex = useMemo(
    () =>
      getSignPlaqueTexture(
        PERSONAL_CONFIG.destinations.gamePortfolioLabel,
        'right',
        PERSONAL_CONFIG.destinations.gamePortfolioUrl ? 'Explore World' : 'In Progress'
      ),
    []
  );

  const materials = useMemo(() => {
    return {
      post: new THREE.MeshStandardMaterial({
        color: '#7A5030',
        roughness: 0.7,
        metalness: 0.04,
        bumpMap: woodBump,
        bumpScale: 0.016,
      }),
      uxBoard: new THREE.MeshStandardMaterial({
        color: '#5B3920',
        roughness: 0.58,
        metalness: 0.05,
        bumpMap: woodBump,
        bumpScale: 0.014,
      }),
      gameBoard: new THREE.MeshStandardMaterial({
        color: '#5B3920',
        roughness: 0.58,
        metalness: 0.05,
        bumpMap: woodBump,
        bumpScale: 0.014,
      }),
      uxLettering: new THREE.MeshStandardMaterial({
        color: '#FAF6EC',
        emissive: '#F4E5C2',
        emissiveIntensity: 0.28,
        roughness: 0.32,
      }),
      gameLettering: new THREE.MeshStandardMaterial({
        color: '#FAF6EC',
        emissive: '#F4E5C2',
        emissiveIntensity: 0.28,
        roughness: 0.32,
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

    // Restrained physical glow & subtle lift on focus/hover
    materials.uxBoard.emissive.set(isUxActive ? '#523418' : '#000000');
    materials.uxBoard.emissiveIntensity = THREE.MathUtils.lerp(
      materials.uxBoard.emissiveIntensity,
      isUxActive ? 0.55 : 0.0,
      delta * 8
    );
    materials.uxLettering.emissiveIntensity = THREE.MathUtils.lerp(
      materials.uxLettering.emissiveIntensity,
      isUxActive ? 0.75 : 0.28,
      delta * 8
    );

    materials.gameBoard.emissive.set(isGameActive ? '#523418' : '#000000');
    materials.gameBoard.emissiveIntensity = THREE.MathUtils.lerp(
      materials.gameBoard.emissiveIntensity,
      isGameActive ? 0.55 : 0.0,
      delta * 8
    );
    materials.gameLettering.emissiveIntensity = THREE.MathUtils.lerp(
      materials.gameLettering.emissiveIntensity,
      isGameActive ? 0.75 : 0.28,
      delta * 8
    );

    if (uxGroupRef.current) {
      uxGroupRef.current.position.y = THREE.MathUtils.lerp(
        uxGroupRef.current.position.y,
        isUxActive ? 0.04 : 0.0,
        delta * 9
      );
    }
    if (gameGroupRef.current) {
      gameGroupRef.current.position.y = THREE.MathUtils.lerp(
        gameGroupRef.current.position.y,
        isGameActive ? 0.04 : 0.0,
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
      if (dist > 10) return; // Ignore camera orbit drags
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

        {/* Flush back-side plaque so label stays readable even at extreme orbit angles */}
        <mesh position={[-1.52, 1.38, -0.66]} rotation={[0, Math.PI + THREE.MathUtils.degToRad(16), 0]}>
          <planeGeometry args={[1.42, 0.42]} />
          <meshStandardMaterial map={uxPlaqueTex} roughness={0.5} />
        </mesh>

        {/* Subtle warm ground highlight ring when hovered/focused */}
        {(uxHovered || activeHover === 'ux') && (
          <mesh position={[-1.52, 0.25, -0.66]} rotation={[-Math.PI / 2, 0, 0]}>
            <ringGeometry args={[0.32, 0.46, 32]} />
            <meshBasicMaterial color="#DCC99D" transparent opacity={0.65} side={THREE.DoubleSide} />
          </mesh>
        )}

        {/* Large invisible click/tap hitbox for reliable smartphone touch */}
        <mesh
          name="Hitbox_Sign_UX"
          position={[-1.52, 1.26, -0.60]}
          rotation={[0, THREE.MathUtils.degToRad(16), 0]}
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

        {/* Flush back-side plaque */}
        <mesh position={[1.52, 1.38, -0.66]} rotation={[0, Math.PI - THREE.MathUtils.degToRad(16), 0]}>
          <planeGeometry args={[1.42, 0.42]} />
          <meshStandardMaterial map={gamePlaqueTex} roughness={0.5} />
        </mesh>

        {/* Subtle warm ground highlight ring when hovered/focused */}
        {(gameHovered || activeHover === 'game') && (
          <mesh position={[1.52, 0.25, -0.66]} rotation={[-Math.PI / 2, 0, 0]}>
            <ringGeometry args={[0.32, 0.46, 32]} />
            <meshBasicMaterial color="#DCC99D" transparent opacity={0.65} side={THREE.DoubleSide} />
          </mesh>
        )}

        {/* Large invisible click/tap hitbox for reliable smartphone touch */}
        <mesh
          name="Hitbox_Sign_Game"
          position={[1.52, 1.26, -0.60]}
          rotation={[0, THREE.MathUtils.degToRad(-16), 0]}
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
