export function Card({ children, className = '', hoverable = false }: { children: React.ReactNode, className?: string, hoverable?: boolean }) {
  return (
    <div className={`bg-[var(--color-surface)] border border-[var(--color-line)] rounded-[8px] premium-shadow ${hoverable ? 'hover-lift cursor-pointer' : ''} ${className}`}>
      {children}
    </div>
  );
}
