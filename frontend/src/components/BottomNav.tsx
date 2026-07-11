import React from 'react';

type Tab = 'dashboard' | 'scanner' | 'charts' | 'news';

interface BottomNavProps {
  activeTab: Tab;
  setActiveTab: (tab: Tab) => void;
}

export const BottomNav: React.FC<BottomNavProps> = ({ activeTab, setActiveTab }) => {
  return (
    <nav style={{
      position: 'fixed',
      bottom: 0,
      left: 0,
      right: 0,
      height: '80px',
      background: 'rgba(15, 23, 42, 0.85)',
      backdropFilter: 'blur(12px)',
      WebkitBackdropFilter: 'blur(12px)',
      borderTop: '1px solid rgba(255, 255, 255, 0.1)',
      display: 'flex',
      justifyContent: 'space-around',
      alignItems: 'center',
      zIndex: 1000,
      paddingBottom: 'env(safe-area-inset-bottom, 16px)'
    }}>
      <NavItem 
        icon="📊" 
        label="Dashboard" 
        isActive={activeTab === 'dashboard'} 
        onClick={() => setActiveTab('dashboard')} 
      />
      <NavItem 
        icon="🛰️" 
        label="Scanner" 
        isActive={activeTab === 'scanner'} 
        onClick={() => setActiveTab('scanner')} 
      />
      <NavItem 
        icon="📈" 
        label="Charts" 
        isActive={activeTab === 'charts'} 
        onClick={() => setActiveTab('charts')} 
      />
      <NavItem 
        icon="📰" 
        label="News" 
        isActive={activeTab === 'news'} 
        onClick={() => setActiveTab('news')} 
      />
    </nav>
  );
};

const NavItem: React.FC<{ icon: string, label: string, isActive: boolean, onClick: () => void }> = ({ icon, label, isActive, onClick }) => {
  return (
    <div 
      onClick={onClick}
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '4px',
        cursor: 'pointer',
        opacity: isActive ? 1 : 0.5,
        transform: isActive ? 'scale(1.05)' : 'scale(1)',
        transition: 'all 0.2s ease',
        width: '25%',
      }}
    >
      <div style={{ fontSize: '1.5rem', filter: isActive ? 'drop-shadow(0 0 8px rgba(255,255,255,0.3))' : 'none' }}>
        {icon}
      </div>
      <div style={{ fontSize: '0.75rem', fontWeight: isActive ? 600 : 400, color: isActive ? '#fff' : '#94a3b8' }}>
        {label}
      </div>
    </div>
  );
};
