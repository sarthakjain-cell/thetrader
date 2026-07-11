import React, { useState, MouseEvent } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface RippleButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  children: React.ReactNode;
  variant?: 'primary' | 'secondary' | 'critical';
}

const RippleButton: React.FC<RippleButtonProps> = ({ children, className = '', variant = 'primary', onClick, ...props }) => {
  const [ripples, setRipples] = useState<{ x: number; y: number; id: number }[]>([]);

  const handleClick = (e: MouseEvent<HTMLButtonElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const newRipple = { x, y, id: Date.now() };

    setRipples((prev) => [...prev, newRipple]);

    if (onClick) {
      onClick(e);
    }
  };

  const variantClass = variant === 'primary' ? 'btn-primary' : (variant === 'secondary' ? 'btn-secondary' : 'btn-critical');

  return (
    <button 
      className={`${variantClass} ${className}`} 
      onClick={handleClick}
      style={{ position: 'relative', overflow: 'hidden' }}
      {...props}
    >
      <span style={{ position: 'relative', zIndex: 1 }}>{children}</span>
      <AnimatePresence>
        {ripples.map((ripple) => (
          <motion.div
            key={ripple.id}
            initial={{ scale: 0, opacity: 0.8 }}
            animate={{ scale: 10, opacity: 0 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.6, ease: "easeOut" }}
            onAnimationComplete={() => {
              setRipples((prev) => prev.filter((r) => r.id !== ripple.id));
            }}
            style={{
              position: 'absolute',
              left: ripple.x,
              top: ripple.y,
              width: 30,
              height: 30,
              marginLeft: -15,
              marginTop: -15,
              borderRadius: '50%',
              background: 'radial-gradient(circle, var(--platinum-glow) 0%, transparent 70%)',
              pointerEvents: 'none',
              zIndex: 0
            }}
          />
        ))}
      </AnimatePresence>
    </button>
  );
};

export default RippleButton;
