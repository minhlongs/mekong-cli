import React, { type ReactNode } from 'react';
import { motion } from 'framer-motion';

export interface RevealProps {
    children: ReactNode;
    direction?: 'up' | 'down' | 'left' | 'right';
    delay?: number;
}

export function Reveal({ children, direction = 'up', delay = 0 }: RevealProps) {
    const directions = {
        up: { y: 60 },
        down: { y: -60 },
        left: { x: 60 },
        right: { x: -60 },
    };

    return (
        <motion.div
            initial={{ opacity: 0, ...directions[direction] }}
            whileInView={{ opacity: 1, x: 0, y: 0 }}
            viewport={{ once: true, margin: '-100px' }}
            transition={{ duration: 0.8, delay, ease: [0.16, 1, 0.3, 1] }}
        >
            {/* @ts-ignore - framer-motion accepts ReactNode at runtime */}
            {children}
        </motion.div>
    );
}
