import React from 'react';

type Tab = 'home' | 'scanner' | 'charts' | 'portfolio' | 'news';

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
      height: '60px',
      background: '#12151c', /* Upstox bottom nav color */
      borderTop: '1px solid rgba(255, 255, 255, 0.05)',
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      zIndex: 1000,
      padding: '0 12px',
      paddingBottom: 'env(safe-area-inset-bottom, 0px)'
    }}>
      <NavItem 
        icon="⌂" 
        label="HOME" 
        isActive={activeTab === 'home'} 
        onClick={() => setActiveTab('home')} 
      />
      <NavItem 
        icon="⚡" 
        label="SCANNER" 
        isActive={activeTab === 'scanner'} 
        onClick={() => setActiveTab('scanner')} 
      />
      <NavItem 
        icon="💼" 
        label="PORTFOLIO" 
        isActive={activeTab === 'portfolio'} 
        onClick={() => setActiveTab('portfolio')} 
      />
      <NavItem 
        icon="📈" 
        label="CHARTS" 
        isActive={activeTab === 'charts'} 
        onClick={() => setActiveTab('charts')} 
      />
      <NavItem 
        icon="📰" 
        label="NEWS" 
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
        color: isActive ? '#5b45ff' : '#8b949e', /* Upstox blurple active color */
        flex: 1,
      }}
    >
      <div style={{ fontSize: '1.2rem', fontWeight: isActive ? 'bold' : 'normal' }}>
        {icon}
      </div>
      <div style={{ fontSize: '0.65rem', fontWeight: isActive ? 600 : 500, letterSpacing: '0.5px' }}>
        {label}
      </div>
    </div>
  );
};
