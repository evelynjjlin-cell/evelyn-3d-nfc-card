import React, { Suspense, useCallback, useEffect, useState } from 'react';
import { Canvas } from '@react-three/fiber';
import * as THREE from 'three';
import {
  CameraViewPreset,
  detectDefaultQuality,
  PERSONAL_CONFIG,
  QualityLevel,
} from './config/personalConfig';
import { ForestEnvironment } from './components/world/ForestEnvironment';
import { SignId } from './components/world/WoodenSigns';
import { IdentityOverlay } from './components/ui/IdentityOverlay';
import { ContactPanel } from './components/ui/ContactPanel';
import { GamePortfolioModal } from './components/ui/GamePortfolioModal';
import { ResponsiveFallback } from './components/ui/ResponsiveFallback';
import { downloadVCard } from './utils/nfcAndVcard';

declare global {
  interface Window {
    __setCrossroadsView?: (preset: CameraViewPreset['id']) => void;
    __openMailboxLetter?: (open: boolean) => void;
    __crossroadsSceneReady?: boolean;
    __r3fRenderNow?: () => string;
  }
}

function checkWebGLAvailable(): boolean {
  if (typeof window === 'undefined') return true;
  try {
    const canvas = document.createElement('canvas');
    return Boolean(
      window.WebGLRenderingContext &&
        (canvas.getContext('webgl2') || canvas.getContext('webgl'))
    );
  } catch {
    return false;
  }
}

function getInitialPresetFromUrl(): CameraViewPreset['id'] {
  if (typeof window === 'undefined') return 'initial';
  const params = new URLSearchParams(window.location.search);
  const view = params.get('view');
  if (
    view === 'initial' ||
    view === 'rotated' ||
    view === 'uxSign' ||
    view === 'gameSign' ||
    view === 'mailbox' ||
    view === 'closeupTrees' ||
    view === 'closeupProps' ||
    view === 'closeupBridgeCreekMailbox' ||
    view === 'closeupSigns'
  ) {
    return view;
  }
  return 'initial';
}

export const App: React.FC = () => {
  const [qualityLevel, setQualityLevel] = useState<QualityLevel>(() => detectDefaultQuality());
  const [cameraPreset, setCameraPreset] = useState<CameraViewPreset['id']>(() =>
    getInitialPresetFromUrl()
  );
  const [activeHover, setActiveHover] = useState<string | null>(null);
  const [isMailboxOpen, setIsMailboxOpen] = useState<boolean>(false);
  const [isContactPanelOpen, setIsContactPanelOpen] = useState<boolean>(false);
  const [isGameModalOpen, setIsGameModalOpen] = useState<boolean>(false);
  const [sceneReady, setSceneReady] = useState<boolean>(false);
  const [webGLSupported, setWebGLSupported] = useState<boolean>(true);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const activeQualityPreset = PERSONAL_CONFIG.qualityPresets[qualityLevel];

  useEffect(() => {
    setWebGLSupported(checkWebGLAvailable());
  }, []);

  useEffect(() => {
    window.__setCrossroadsView = (preset: CameraViewPreset['id']) => {
      setCameraPreset(preset);
    };
    window.__openMailboxLetter = (open: boolean) => {
      setIsMailboxOpen(open);
      setIsContactPanelOpen(open);
    };
    return () => {
      delete window.__setCrossroadsView;
      delete window.__openMailboxLetter;
    };
  }, []);

  const showToast = useCallback((msg: string) => {
    setToastMessage(msg);
  }, []);

  useEffect(() => {
    if (!toastMessage) return;
    const timer = window.setTimeout(() => setToastMessage(null), 3800);
    return () => window.clearTimeout(timer);
  }, [toastMessage]);

  const handleSelectSign = useCallback((id: SignId) => {
    const { destinations } = PERSONAL_CONFIG;
    if (id === 'ux') {
      setCameraPreset('uxSign');
      window.open(destinations.uxPortfolioUrl, '_blank', 'noopener,noreferrer');
    } else if (id === 'game') {
      const configuredGameUrl = destinations.gamePortfolioUrl.trim();
      if (configuredGameUrl && /^https?:\/\//i.test(configuredGameUrl)) {
        setCameraPreset('gameSign');
        window.open(configuredGameUrl, '_blank', 'noopener,noreferrer');
      } else {
        setIsGameModalOpen(true);
      }
    }
  }, []);

  const handleSelectMailbox = useCallback(() => {
    setIsMailboxOpen(true);
    const reducedMotion =
      typeof window !== 'undefined' &&
      window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
    if (reducedMotion) {
      setIsContactPanelOpen(true);
    } else {
      window.setTimeout(() => {
        setIsContactPanelOpen(true);
      }, 280);
    }
  }, []);

  const handleCloseContactPanel = useCallback(() => {
    setIsContactPanelOpen(false);
    setIsMailboxOpen(false);
  }, []);

  const handleQuickSaveContact = useCallback(() => {
    const res = downloadVCard();
    showToast(res.message);
  }, [showToast]);

  const handleSceneReady = useCallback(() => {
    setSceneReady(true);
    window.__crossroadsSceneReady = true;
  }, []);

  return (
    <main className="app-viewport">
      {/* Real-Time 3D Forest Collectible Canvas */}
      {webGLSupported ? (
        <div className="canvas-wrapper" aria-label="Interactive 3D Forest Crossroads Collectible">
          <Canvas
            shadows={activeQualityPreset.shadows}
            dpr={activeQualityPreset.dpr}
            camera={{
              fov: 40,
              near: 0.2,
              far: 65,
              position: [0, 7.8, 16.5],
            }}
            gl={{
              antialias: true,
              alpha: false,
              preserveDrawingBuffer: true,
              powerPreference: 'high-performance',
              toneMapping: THREE.ACESFilmicToneMapping,
              toneMappingExposure: 1.08,
            }}
            onCreated={({ gl, scene, camera, advance }) => {
              gl.setClearColor('#173229', 1);
              window.__r3fRenderNow = () => {
                for (let i = 0; i < 36; i++) {
                  advance(performance.now() + i * 16);
                }
                gl.render(scene, camera);
                return JSON.stringify({
                  children: scene.children.length,
                  camPos: camera.position.toArray().map((n) => Number(n.toFixed(2))),
                });
              };
            }}
          >
            <Suspense fallback={null}>
              <ForestEnvironment
                quality={activeQualityPreset}
                cameraPreset={cameraPreset}
                activeHover={activeHover}
                isMailboxOpen={isMailboxOpen}
                onHoverChange={setActiveHover}
                onSelectSign={handleSelectSign}
                onSelectMailbox={handleSelectMailbox}
                onSceneReady={handleSceneReady}
              />
            </Suspense>
          </Canvas>
          {!sceneReady && (
            <ResponsiveFallback
              mode="loading"
              onOpenContact={() => setIsContactPanelOpen(true)}
              onOpenGamePlaceholder={() => setIsGameModalOpen(true)}
            />
          )}
        </div>
      ) : (
        <ResponsiveFallback
          mode="webgl-unavailable"
          onOpenContact={() => setIsContactPanelOpen(true)}
          onOpenGamePlaceholder={() => setIsGameModalOpen(true)}
        />
      )}

      {/* Minimal Collectible Controls & Screen-Reader Accessible Identity Equivalent */}
      <IdentityOverlay
        activeQuality={qualityLevel}
        onChangeQuality={setQualityLevel}
        activeCameraPreset={cameraPreset}
        onChangeCameraPreset={setCameraPreset}
        activeHover={activeHover}
        onHoverNav={setActiveHover}
        onTriggerSign={handleSelectSign}
        onTriggerMailbox={handleSelectMailbox}
        onQuickSaveContact={handleQuickSaveContact}
        toastMessage={toastMessage}
      />

      {/* Physical-Looking Animated Woodland Contact Letter */}
      <ContactPanel
        isOpen={isContactPanelOpen}
        onClose={handleCloseContactPanel}
        onStatusToast={showToast}
      />

      {/* Play Path Placeholder Modal ("New world in progress.") */}
      <GamePortfolioModal
        isOpen={isGameModalOpen}
        onClose={() => setIsGameModalOpen(false)}
        onOpenContact={() => {
          setIsMailboxOpen(true);
          setIsContactPanelOpen(true);
        }}
      />
    </main>
  );
};
