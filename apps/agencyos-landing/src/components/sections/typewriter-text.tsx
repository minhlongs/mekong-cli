"use client";

import { useEffect, useState } from "react";

interface TypewriterTextProps {
  texts: string[];
  typingSpeed?: number;
  deletingSpeed?: number;
  pauseDuration?: number;
}

export function TypewriterText({
  texts,
  typingSpeed = 100,
  deletingSpeed = 50,
  pauseDuration = 2000,
}: TypewriterTextProps) {
  const [currentTextIndex, setCurrentTextIndex] = useState(0);
  const [currentText, setCurrentText] = useState("");
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    const text = texts[currentTextIndex];

    const timeout = setTimeout(
      () => {
        if (!isDeleting) {
          if (currentText.length < text.length) {
            setCurrentText(text.slice(0, currentText.length + 1));
          } else {
            setTimeout(() => setIsDeleting(true), pauseDuration);
          }
        } else {
          if (currentText.length > 0) {
            setCurrentText(text.slice(0, currentText.length - 1));
          } else {
            setIsDeleting(false);
            setCurrentTextIndex((prev) => (prev + 1) % texts.length);
          }
        }
      },
      isDeleting ? deletingSpeed : typingSpeed
    );

    return () => clearTimeout(timeout);
  }, [currentText, isDeleting, currentTextIndex, texts, typingSpeed, deletingSpeed, pauseDuration]);

  return (
    <span className="inline-block">
      {currentText}
      <span className="animate-pulse">|</span>
    </span>
  );
}
