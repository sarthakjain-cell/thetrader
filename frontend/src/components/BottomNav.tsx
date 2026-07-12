import React from 'react';
import { motion } from 'framer-motion';

type Tab = 'home' | 'scanner' | 'charts' | 'portfolio' | 'news';

interface BottomNavProps {
  activeTab: Tab;
  setActiveTab: (tab: Tab) => void;
}

export const BottomNav: React.FC<BottomNavProps> = ({ activeTab, setActiveTab }) => {
  return (
    <nav style={{
      position: 'fixed',
      bottom: '20px',
      left: '50%',
      transform: 'translateX(-50%)',
      width: 'max-content',
      maxWidth: '90%',
      height: '65px',
      background: 'rgba(18, 21, 28, 0.85)',
      backdropFilter: 'blur(12px)',
      border: '1px solid rgba(255, 255, 255, 0.1)',
      borderRadius: '32px',
      boxShadow: '0 8px 32px rgba(0, 0, 0, 0.4)',
      display: 'flex',
      justifyContent: 'center',
      gap: '12px',
      alignItems: 'center',
      zIndex: 1000,
      padding: '0 16px',
      paddingBottom: 'env(safe-area-inset-bottom, 0px)'
    }}>
      <NavItem 
        icon={<HomeIcon isActive={activeTab === 'home'} />} 
        label="HOME" 
        isActive={activeTab === 'home'} 
        onClick={() => setActiveTab('home')} 
      />
      <NavItem 
        icon={<RadarIcon isActive={activeTab === 'scanner'} />} 
        label="AI RADAR" 
        isActive={activeTab === 'scanner'} 
        onClick={() => setActiveTab('scanner')} 
      />
      <NavItem 
        icon={<PortfolioIcon isActive={activeTab === 'portfolio'} />} 
        label="PORTFOLIO" 
        isActive={activeTab === 'portfolio'} 
        onClick={() => setActiveTab('portfolio')} 
      />
      <NavItem 
        icon={<ChartIcon isActive={activeTab === 'charts'} />} 
        label="CHARTS" 
        isActive={activeTab === 'charts'} 
        onClick={() => setActiveTab('charts')} 
      />
      <NavItem 
        icon={<NewsIcon isActive={activeTab === 'news'} />} 
        label="NEWS" 
        isActive={activeTab === 'news'} 
        onClick={() => setActiveTab('news')} 
      />
    </nav>
  );
};

const NavItem: React.FC<{ icon: React.ReactNode, label: string, isActive: boolean, onClick: () => void }> = ({ icon, label, isActive, onClick }) => {
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
        color: isActive ? '#5b45ff' : '#8b949e',
        width: '56px',
        position: 'relative',
        height: '100%',
        paddingTop: '8px'
      }}
    >
      <motion.div
        animate={{ 
          y: isActive ? -4 : 0,
          scale: isActive ? 1.1 : 1
        }}
        transition={{ type: "spring", stiffness: 300, damping: 20 }}
      >
        {icon}
      </motion.div>
      <span style={{ 
        fontSize: '0.65rem', 
        fontWeight: isActive ? 700 : 500, 
        letterSpacing: '0.5px',
        opacity: isActive ? 1 : 0.7
      }}>
        {label}
      </span>
      {isActive && (
        <motion.div 
          layoutId="activeTabIndicator"
          style={{
            position: 'absolute',
            bottom: '-4px',
            width: '4px',
            height: '4px',
            background: '#5b45ff',
            borderRadius: '50%',
            boxShadow: '0 0 10px rgba(91, 69, 255, 0.8)'
          }}
        />
      )}
    </div>
  );
};

// --- SVG Icons ---

const HomeIcon = ({ isActive }: { isActive: boolean }) => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={isActive ? "2.5" : "2"} strokeLinecap="round" strokeLinejoin="round">
    <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path>
    <polyline points="9 22 9 12 15 12 15 22"></polyline>
  </svg>
);

const RadarIcon = ({ isActive }: { isActive: boolean }) => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={isActive ? "2.5" : "2"} strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10"></circle>
    <circle cx="12" cy="12" r="6"></circle>
    <circle cx="12" cy="12" r="2"></circle>
    {isActive && (
      <motion.line 
        x1="12" y1="12" x2="12" y2="2" 
        stroke="#5b45ff"
        animate={{ rotate: 360 }}
        transition={{ repeat: Infinity, duration: 2, ease: "linear" }}
        style={{ transformOrigin: '12px 12px' }}
      />
    )}
  </svg>
);

const PortfolioIcon = ({ isActive }: { isActive: boolean }) => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={isActive ? "2.5" : "2"} strokeLinecap="round" strokeLinejoin="round">
    <rect x="2" y="7" width="20" height="14" rx="2" ry="2"></rect>
    <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"></path>
  </svg>
);

const ChartIcon = ({ isActive }: { isActive: boolean }) => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={isActive ? "2.5" : "2"} strokeLinecap="round" strokeLinejoin="round">
    <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
  </svg>
);

const NewsIcon = ({ isActive }: { isActive: boolean }) => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={isActive ? "2.5" : "2"} strokeLinecap="round" strokeLinejoin="round">
    <path d="M4 22h16a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2H8a2 2 0 0 0-2 2v16a2 2 0 0 1-2 2Zm0 0a2 2 0 0 1-2-2v-9c0-1.1.9-2 2-2h2"></path>
    <path d="M18 14h-8"></path>
    <path d="M15 18h-5"></path>
    <path d="M10 6h8v4h-8V6Z"></path>
  </svg>
);
