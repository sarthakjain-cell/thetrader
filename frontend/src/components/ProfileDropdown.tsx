import React, { useState, useRef, useEffect } from 'react';
import styles from './ProfileDropdown.module.css';
import { motion, AnimatePresence } from 'framer-motion';

export const ProfileDropdown: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown if clicked outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    
    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  return (
    <div className={styles.container} ref={dropdownRef}>
      <div 
        className={styles.avatar} 
        onClick={() => setIsOpen(!isOpen)}
        title="Profile & Settings"
      >
        SJ
      </div>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: -10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -10, scale: 0.95 }}
            transition={{ duration: 0.2 }}
            className={styles.dropdown}
          >
            <div className={styles.menuItem} onClick={() => setIsOpen(false)}>
              👤 Profile
            </div>
            <div className={styles.menuItem} onClick={() => setIsOpen(false)}>
              ⚙️ Settings
            </div>
            <div className={styles.menuItem} onClick={() => setIsOpen(false)}>
              💳 Subscription
            </div>
            
            <div className={styles.divider}></div>
            
            <div className={`${styles.menuItem} ${styles.logout}`} onClick={() => setIsOpen(false)}>
              🚪 Log Out
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
