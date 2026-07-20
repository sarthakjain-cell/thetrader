import React from 'react';
import Link from 'next/link';
import styles from './ProfileDropdown.module.css';

export const ProfileDropdown: React.FC = () => {
  return (
    <Link href="/profile" style={{ textDecoration: 'none' }}>
      <div 
        className={styles.avatar} 
        title="Profile & Settings"
      >
        SJ
      </div>
    </Link>
  );
};
