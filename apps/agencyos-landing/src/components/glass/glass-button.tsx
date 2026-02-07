"use client";

import { cn } from "@/lib/utils";
import { cva, type VariantProps } from "class-variance-authority";
import { motion, useMotionValue, useSpring } from "framer-motion";
import { ButtonHTMLAttributes, forwardRef, useRef } from "react";

const buttonVariants = cva(
  "relative inline-flex items-center justify-center rounded-full font-medium transition-all duration-300 overflow-hidden",
  {
    variants: {
      variant: {
        primary: "bg-gradient-to-r from-purple-500 to-blue-500 text-white hover:shadow-2xl hover:shadow-purple-500/50",
        glass: "glass-effect hover:bg-glass-200 text-white",
        outline: "border-2 border-white/20 hover:border-white/40 hover:bg-glass-100 text-white",
      },
      size: {
        sm: "px-4 py-2 text-sm",
        md: "px-6 py-3 text-base",
        lg: "px-8 py-4 text-lg",
      },
      magnetic: {
        true: "cursor-pointer",
        false: "",
      },
    },
    defaultVariants: {
      variant: "primary",
      size: "md",
      magnetic: false,
    },
  }
);

export interface GlassButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

export const GlassButton = forwardRef<HTMLButtonElement, GlassButtonProps>(
  ({ className, variant, size, magnetic, children, onClick, type, disabled, ...htmlProps }, ref) => {
    const buttonRef = useRef<HTMLButtonElement>(null);
    const x = useMotionValue(0);
    const y = useMotionValue(0);

    const springConfig = { damping: 20, stiffness: 300 };
    const springX = useSpring(x, springConfig);
    const springY = useSpring(y, springConfig);

    const handleMouseMove = (e: React.MouseEvent<HTMLButtonElement>) => {
      if (!magnetic || !buttonRef.current) return;

      const rect = buttonRef.current.getBoundingClientRect();
      const centerX = rect.left + rect.width / 2;
      const centerY = rect.top + rect.height / 2;

      const distanceX = e.clientX - centerX;
      const distanceY = e.clientY - centerY;

      x.set(distanceX * 0.3);
      y.set(distanceY * 0.3);
    };

    const handleMouseLeave = () => {
      x.set(0);
      y.set(0);
    };

    return (
      <motion.button
        ref={buttonRef}
        className={cn(buttonVariants({ variant, size, magnetic }), className)}
        style={magnetic ? { x: springX, y: springY } : {}}
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
        onClick={onClick}
        type={type}
        disabled={disabled}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
      >
        {children}
      </motion.button>
    );
  }
);

GlassButton.displayName = "GlassButton";
