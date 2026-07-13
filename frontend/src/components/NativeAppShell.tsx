"use client";

import React, { useEffect } from 'react';
import { Capacitor } from '@capacitor/core';
import { StatusBar, Style } from '@capacitor/status-bar';
import { SplashScreen } from '@capacitor/splash-screen';
import { App } from '@capacitor/app';

export const NativeAppShell: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  useEffect(() => {
    if (!Capacitor.isNativePlatform()) return;

    const setupNative = async () => {
      try {
        // Set Status Bar to overlay the webview and use light text (for dark theme)
        await StatusBar.setStyle({ style: Style.Dark });
        await StatusBar.setOverlaysWebView({ overlay: true });
        
        // Hide splash screen after React mounts
        await SplashScreen.hide();
      } catch (err) {
        console.warn("Native setup error:", err);
      }
    };

    setupNative();

    let isInitialLaunch = true;
    
    // Handle backgrounding: SSE closes when iOS/Android suspends the app.
    // When the app comes back to active, we reload to establish a fresh SSE connection.
    const listener = App.addListener('appStateChange', ({ isActive }) => {
      if (isActive) {
        if (!isInitialLaunch) {
          window.location.reload();
        }
      } else {
        isInitialLaunch = false;
      }
    });

    return () => {
      listener.then(l => l.remove());
    };
  }, []);

  return <>{children}</>;
};
