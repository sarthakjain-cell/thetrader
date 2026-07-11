"use client";

import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { Capacitor } from '@capacitor/core';
import { LocalNotifications } from '@capacitor/local-notifications';

export interface Alert {
  id: string;
  type: 'info' | 'critical' | 'success';
  message: string;
  timestamp: number;
}

interface AlertContextType {
  alerts: Alert[];
  addAlert: (alert: Omit<Alert, 'timestamp'>) => void;
  clearAlerts: () => void;
}

const AlertContext = createContext<AlertContextType | undefined>(undefined);

export const AlertProvider = ({ children }: { children: ReactNode }) => {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [permission, setPermission] = useState<NotificationPermission>('default');

  useEffect(() => {
    if (Capacitor.isNativePlatform()) {
      LocalNotifications.requestPermissions().then(res => {
        setPermission(res.display === 'granted' ? 'granted' : 'default');
      });
    } else if ('Notification' in window) {
      Notification.requestPermission().then(setPermission);
    }
  }, []);

  const playSound = (type: string) => {
    if (typeof window !== 'undefined' && localStorage.getItem('algo_mute') === 'true') return;
    
    try {
      // In a real app, load actual audio files. For now, synthetic beep.
      const ctx = new (window.AudioContext || (window as any).webkitAudioContext)();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.type = type === 'critical' ? 'sawtooth' : 'sine';
      osc.frequency.setValueAtTime(type === 'critical' ? 400 : 800, ctx.currentTime);
      gain.gain.setValueAtTime(0.1, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.5);
      osc.start(ctx.currentTime);
      osc.stop(ctx.currentTime + 0.5);
    } catch (e) {
      console.warn("Audio context failed", e);
    }
  };

  const addAlert = (alert: Omit<Alert, 'timestamp'>) => {
    const newAlert = { ...alert, timestamp: Date.now() };
    
    setAlerts(prev => {
      // Prevent exact duplicates within last minute
      const isDuplicate = prev.some(a => a.id === alert.id && (Date.now() - a.timestamp < 60000));
      if (isDuplicate) return prev;

      // Trigger OS Notification
      if (permission === 'granted') {
        if (Capacitor.isNativePlatform()) {
           LocalNotifications.schedule({
             notifications: [
               {
                 title: "AlgoTrade Terminal",
                 body: alert.message,
                 id: Math.floor(Date.now() / 1000), // Capacitor expects i32 int
               }
             ]
           });
        } else {
           new Notification("AlgoTrade Terminal", { body: alert.message });
        }
      }

      // Trigger Sound
      playSound(alert.type);

      return [newAlert, ...prev].slice(0, 50); // Keep last 50
    });
  };

  const clearAlerts = () => setAlerts([]);

  return (
    <AlertContext.Provider value={{ alerts, addAlert, clearAlerts }}>
      {children}
    </AlertContext.Provider>
  );
};

export const useAlerts = () => {
  const context = useContext(AlertContext);
  if (!context) throw new Error("useAlerts must be used within AlertProvider");
  return context;
};
