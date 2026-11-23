import React, { useEffect, useRef } from 'react';
import { useFrame, useThree } from '@react-three/fiber';
import { OrbitControls } from '@react-three/drei';
import * as THREE from 'three';
import type { OrbitControls as OrbitControlsImpl } from 'three-stdlib';
import { CameraViewPreset, PERSONAL_CONFIG } from '../../config/personalConfig';

interface CameraControllerProps {
  activePreset: CameraViewPreset['id'];
  hoverFocus: string | null;
  enableIdleMotion: boolean;
  onUserOrbit?: () => void;
}

export const CameraController: React.FC<CameraControllerProps> = ({
  activePreset,
  hoverFocus,
  enableIdleMotion,
  onUserOrbit,
}) => {
  const controlsRef = useRef<OrbitControlsImpl>(null);
  const { camera, size } = useThree();

  const isTransitioning = useRef(true);
  const userInteracting = useRef(false);
  const sphericalGoal = useRef(new THREE.Spherical(13.5, 1.04, -0.04));
  const targetGoal = useRef(new THREE.Vector3(0, 0.35, 0.15));

  const isPortraitMobile = size.width < 768 || size.width / Math.max(1, size.height) < 0.78;

  // Compute responsive camera distance so narrow portrait phones frame the whole island cleanly
  const computeResponsiveDistance = (preset: CameraViewPreset): number => {
    const aspect = size.width / Math.max(1, size.height);
    if (aspect < 0.56) {
      // e.g., 390x844 (aspect ~0.462)
      return preset.distanceMobile * (0.48 / Math.max(0.36, aspect)) * 0.96;
    }
    if (isPortraitMobile) {
      return preset.distanceMobile;
    }
    return preset.distanceDesktop;
  };

  useEffect(() => {
    const preset = PERSONAL_CONFIG.cameraPresets[activePreset] || PERSONAL_CONFIG.cameraPresets.initial;
    const dist = computeResponsiveDistance(preset);
    sphericalGoal.current.set(dist, preset.polar, preset.azimuth);
    targetGoal.current.set(
      preset.target[0],
      isPortraitMobile ? preset.target[1] + 0.12 : preset.target[1],
      preset.target[2]
    );
    isTransitioning.current = true;
  }, [activePreset, size.width, size.height, isPortraitMobile]);

  // Apply initial camera position immediately on first mount so the very first frame is composed
  useEffect(() => {
    const preset = PERSONAL_CONFIG.cameraPresets[activePreset] || PERSONAL_CONFIG.cameraPresets.initial;
    const dist = computeResponsiveDistance(preset);
    const sph = new THREE.Spherical(dist, preset.polar, preset.azimuth);
    const targetVec = new THREE.Vector3(
      preset.target[0],
      isPortraitMobile ? preset.target[1] + 0.12 : preset.target[1],
      preset.target[2]
    );
    const offset = new THREE.Vector3().setFromSpherical(sph);
    camera.position.copy(targetVec).add(offset);
    camera.lookAt(targetVec);
    if (controlsRef.current) {
      controlsRef.current.target.copy(targetVec);
      controlsRef.current.update();
    }
  }, []);

  useFrame(({ clock }, delta) => {
    const controls = controlsRef.current;
    if (!controls) return;

    if (!userInteracting.current && isTransitioning.current) {
      // Smoothly interpolate target and camera spherical position toward the goal preset
      controls.target.lerp(targetGoal.current, Math.min(1, delta * 6.5));

      const offset = camera.position.clone().sub(controls.target);
      const currentSph = new THREE.Spherical().setFromVector3(offset);

      // Gentle hover nudge when hovering a sign or mailbox
      let hoverAzimuthOffset = 0;
      if (hoverFocus === 'ux') hoverAzimuthOffset = -0.035;
      else if (hoverFocus === 'game') hoverAzimuthOffset = 0.035;
      else if (hoverFocus === 'mailbox') hoverAzimuthOffset = 0.025;

      const idleAzimuth =
        enableIdleMotion && !hoverFocus ? Math.sin(clock.getElapsedTime() * 0.45) * 0.014 : 0;

      const desiredTheta = sphericalGoal.current.theta + hoverAzimuthOffset + idleAzimuth;
      const desiredPhi = sphericalGoal.current.phi;
      const desiredRadius = sphericalGoal.current.radius;

      currentSph.theta = THREE.MathUtils.lerp(currentSph.theta, desiredTheta, Math.min(1, delta * 5.5));
      currentSph.phi = THREE.MathUtils.lerp(currentSph.phi, desiredPhi, Math.min(1, delta * 5.5));
      currentSph.radius = THREE.MathUtils.lerp(
        currentSph.radius,
        desiredRadius,
        Math.min(1, delta * 5.5)
      );

      const newOffset = new THREE.Vector3().setFromSpherical(currentSph);
      camera.position.copy(controls.target).add(newOffset);
      controls.update();

      const err =
        Math.abs(currentSph.theta - desiredTheta) +
        Math.abs(currentSph.phi - desiredPhi) +
        Math.abs(currentSph.radius - desiredRadius) * 0.1;
      if (err < 0.002 && !hoverFocus && !enableIdleMotion) {
        isTransitioning.current = false;
      }
    } else {
      controls.update();
    }
  });

  return (
    <OrbitControls
      ref={controlsRef}
      makeDefault
      enablePan={false}
      enableDamping
      dampingFactor={0.07}
      rotateSpeed={0.65}
      zoomSpeed={0.7}
      minDistance={8.2}
      maxDistance={23.5}
      minPolarAngle={0.62}
      maxPolarAngle={1.26}
      minAzimuthAngle={-1.08}
      maxAzimuthAngle={1.08}
      onStart={() => {
        userInteracting.current = true;
        isTransitioning.current = false;
        onUserOrbit?.();
      }}
      onEnd={() => {
        userInteracting.current = false;
      }}
    />
  );
};
