import React from 'react';

type DataTableProps = {
  headers: string[];
  rows: React.ReactNode[][];
  className?: string;
};

export function DataTable({ headers, rows, className = '' }: DataTableProps) {
  return (
    <div className={`w-full overflow-x-auto border border-[var(--color-line)] rounded-[6px] bg-[var(--color-surface)] shadow-[0_1px_3px_rgba(0,0,0,0.05)] ${className}`}>
      <table className="w-full text-left border-collapse text-body">
        <thead className="bg-[var(--color-canvas)] border-b border-[var(--color-line)] relative z-10">
          <tr>
            {headers.map((headerText, i) => (
              <th 
                key={i} 
                className="px-4 py-2 h-[40px] font-semibold text-[var(--color-ink)] sticky top-0 bg-[var(--color-canvas)] whitespace-nowrap"
              >
                <div className="flex items-center gap-2 cursor-pointer hover:text-[var(--color-primary)] transition-colors group">
                  {headerText}
                  {/* Subtle sort icon placeholder */}
                  <span className="text-[10px] opacity-0 group-hover:opacity-100 transition-opacity">▲</span>
                </div>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr 
              key={i} 
              // Zebra rows at 4% ink tint as requested in uiux.md
              className={`h-[40px] border-b border-[var(--color-line)] last:border-0 ${i % 2 === 0 ? '' : 'bg-[var(--color-ink)]/[0.04]'}`}
            >
              {row.map((cell, j) => (
                <td key={j} className="px-4 py-2 align-middle text-[var(--color-ink)]/90">
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
