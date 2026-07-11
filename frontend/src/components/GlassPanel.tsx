import React, { useRef, MouseEvent, ReactNode } from 'react';

interface GlassPanelProps extends React.HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
  as?: keyof JSX.IntrinsicElements;
}

const GlassPanel: React.FC<GlassPanelProps> = ({ children, className = '', as: Component = 'div', style, ...props }) => {
  const panelRef = useRef<HTMLElement>(null);
  const rafRef = useRef<number>();

  const handleMouseMove = (e: MouseEvent<HTMLElement>) => {
    // Only apply on devices with hover capability (desktop)
    if (window.matchMedia && window.matchMedia('(hover: none)').matches) return;
    
    if (!panelRef.current) return;

    const { left, top, width, height } = panelRef.current.getBoundingClientRect();
    const x = e.clientX - left;
    const y = e.clientY - top;

    // Calculate rotation (-5 to 5 degrees) based on mouse position relative to center
    const centerX = width / 2;
    const centerY = height / 2;
    const rotateX = -((y - centerY) / centerY) * 3;
    const rotateY = ((x - centerX) / centerX) * 3;

    if (rafRef.current) cancelAnimationFrame(rafRef.current);
    
    rafRef.current = requestAnimationFrame(() => {
      if (panelRef.current) {
        panelRef.current.style.setProperty('--rotate-x', `${rotateX}deg`);
        panelRef.current.style.setProperty('--rotate-y', `${rotateY}deg`);
        panelRef.current.style.willChange = 'transform';
      }
    });
  };

  const handleMouseLeave = () => {
    if (rafRef.current) cancelAnimationFrame(rafRef.current);
    
    rafRef.current = requestAnimationFrame(() => {
      if (panelRef.current) {
        panelRef.current.style.setProperty('--rotate-x', '0deg');
        panelRef.current.style.setProperty('--rotate-y', '0deg');
        panelRef.current.style.willChange = 'auto';
      }
    });
  };

  return (
    <Component
      ref={panelRef as any}
      className={`glass-panel ${className}`}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      style={style}
      {...props}
    >
      {children}
    </Component>
  );
};

export default GlassPanel;
