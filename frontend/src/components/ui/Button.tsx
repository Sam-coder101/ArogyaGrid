import React from 'react';

type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: 'primary' | 'secondary' | 'accent';
};

export function Button({ variant = 'primary', className = '', children, ...props }: ButtonProps) {
  let styles = '';
  
  if (variant === 'primary') {
    styles = 'bg-[var(--color-primary)] text-[var(--color-surface)] border border-[var(--color-primary)] btn-primary-anim shadow-sm';
  } else if (variant === 'secondary') {
    styles = 'bg-transparent text-[var(--color-primary)] border border-[var(--color-primary)] hover:bg-[var(--color-primary)]/10 transition-colors shadow-sm';
  } else if (variant === 'accent') {
    styles = 'bg-[var(--color-accent)] text-white hover:brightness-110 border border-transparent font-bold transition-all shadow-sm';
  }

  return (
    <button 
      className={`inline-flex items-center justify-center gap-2 px-4 py-2 rounded-[8px] text-caption font-semibold ${styles} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}
