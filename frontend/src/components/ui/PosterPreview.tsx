import React from 'react';
import { Button } from './Button';

type PosterPreviewProps = {
  imageUrl: string;
  caption: string;
  className?: string;
};

export function PosterPreview({ imageUrl, caption, className = '' }: PosterPreviewProps) {
  return (
    <div className={`bg-[var(--color-surface)] border border-[var(--color-line)] rounded-[6px] overflow-hidden shadow-sm flex flex-col ${className}`}>
      {/* Full-bleed Imagen output */}
      <div className="w-full aspect-[4/5] bg-[var(--color-canvas)] relative border-b border-[var(--color-line)] overflow-hidden">
        {/* Using a standard img tag for simplicity, in a real Next.js app we might use next/image but this keeps it portable */}
        <img 
          src={imageUrl} 
          alt={caption}
          className="w-full h-full object-cover"
        />
      </div>
      
      <div className="p-4 flex flex-col gap-4">
        {/* One-line caption */}
        <p className="text-body font-medium text-[var(--color-ink)] truncate" title={caption}>
          {caption}
        </p>
        
        {/* Two actions: Download / Share on WhatsApp */}
        <div className="flex gap-2">
          <Button variant="primary" className="flex-1">
            Download
          </Button>
          <Button variant="secondary" className="flex-1">
            WhatsApp
          </Button>
        </div>
      </div>
    </div>
  );
}
