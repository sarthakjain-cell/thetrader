"use client";

import { useEffect } from 'react';
import { SplashScreen } from '@capacitor/splash-screen';
import { Capacitor } from '@capacitor/core';

export function SplashHider() {
  useEffect(() => {
    // Hide the splash screen once the React app has successfully hydrated
    if (Capacitor.isNativePlatform()) {
      // Add a 600ms delay to ensure all CSS transitions and layouts are stable
      setTimeout(() => {
        SplashScreen.hide();
      }, 600);
    }
  }, []);

  return null;
}
