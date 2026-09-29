import { ReactNode } from 'react';

type BadgeProps = {
  variant?: 'critical' | 'ok' | 'accent' | 'neutral';
  icon?: ReactNode;
  children: ReactNode;
};

export function Badge({ variant = 'neutral', icon, children }: BadgeProps) {
  let bgColor = 'var(--color-canvas)';
  let textColor = 'var(--color-ink)';

  if (variant === 'critical') {
    bgColor = 'var(--color-signal-critical)';
    textColor = 'var(--color-surface)';
  } else if (variant === 'ok') {
    bgColor = 'var(--color-signal-ok)';
    textColor = 'var(--color-surface)';
  } else if (variant === 'accent') {
    bgColor = 'var(--color-accent)';
    textColor = 'var(--color-ink)';
  }

  return (
    <span 
      className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-sm text-caption"
      style={{ backgroundColor: bgColor, color: textColor }}
    >
      {icon && <span aria-hidden="true">{icon}</span>}
      {children}
    </span>
  );
}
