import React, { useState, useEffect } from 'react';

interface Props {
  isOpen: boolean;
  onClose: () => void;
}

export const SettingsModal: React.FC<Props> = ({ isOpen, onClose }) => {
  const [muteAudio, setMuteAudio] = useState(false);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const savedMute = localStorage.getItem('algo_mute') === 'true';
      setMuteAudio(savedMute);
    }
  }, []);

  const handleSave = () => {
    localStorage.setItem('algo_mute', muteAudio.toString());
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div style={{
      position: 'fixed', top: 0, left: 0, width: '100vw', height: '100vh',
      background: 'rgba(0,0,0,0.5)', zIndex: 100, display: 'flex', justifyContent: 'center', alignItems: 'center'
    }}>
      <div className="glass-panel" style={{ width: '400px', padding: 'var(--space-6)', background: 'var(--bg-color)' }}>
        <h2 style={{ marginTop: 0, marginBottom: 'var(--space-6)', color: 'var(--text-primary)' }}>Preferences</h2>
        


        <div style={{ marginBottom: 'var(--space-6)' }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', color: 'var(--text-secondary)' }}>
            <input type="checkbox" checked={muteAudio} onChange={(e) => setMuteAudio(e.target.checked)} />
            Mute Alert Audio
          </label>
        </div>

        <div className="flex-between">
          <button onClick={onClose} style={{ padding: '8px 16px', background: 'transparent', color: 'var(--text-muted)', border: 'none', cursor: 'pointer' }}>Cancel</button>
          <button onClick={handleSave} style={{ padding: '8px 16px', background: 'var(--accent-info)', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>Save Settings</button>
        </div>
      </div>
    </div>
  );
};
