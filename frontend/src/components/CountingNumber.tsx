import React, { useEffect, useRef } from 'react';
import { useSpring, motion, useReducedMotion } from 'framer-motion';

interface CountingNumberProps {
  value: number;
  format?: (val: number) => string;
}

const CountingNumber: React.FC<CountingNumberProps> = React.memo(({ value, format }) => {
  const nodeRef = useRef<HTMLSpanElement>(null);
  const prefersReducedMotion = useReducedMotion();
  
  const springValue = useSpring(value, {
    mass: 1,
    stiffness: 75,
    damping: 15
  });

  useEffect(() => {
    if (prefersReducedMotion) {
      springValue.jump(value);
    } else {
      springValue.set(value);
    }
  }, [value, springValue, prefersReducedMotion]);

  useEffect(() => {
    return springValue.on("change", (latest) => {
      if (nodeRef.current) {
        nodeRef.current.textContent = format ? format(latest) : latest.toFixed(2);
      }
    });
  }, [springValue, format]);

  return <motion.span ref={nodeRef}>{format ? format(value) : value.toFixed(2)}</motion.span>;
}, (prevProps, nextProps) => prevProps.value === nextProps.value);

export default CountingNumber;
