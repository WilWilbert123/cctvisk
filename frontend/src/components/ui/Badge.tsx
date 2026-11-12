import React from 'react';

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'info' | 'outline';
  size?: 'sm' | 'md';
  dot?: boolean;
  children: React.ReactNode;
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({
  variant = 'default',
  size = 'sm',
  dot = false,
  children,
  className = '',
  ...props
}) => {
  const variants: Record<string, string> = {
    default:
      'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300 border-slate-200 dark:border-slate-700',
    success:
      'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800/70',
    warning:
      'bg-amber-50 text-amber-700 dark:bg-amber-950/60 dark:text-amber-300 border-amber-200 dark:border-amber-800/70',
    danger:
      'bg-red-50 text-red-700 dark:bg-red-950/60 dark:text-red-300 border-red-200 dark:border-red-800/70',
    info:
      'bg-blue-50 text-blue-700 dark:bg-blue-950/60 dark:text-blue-300 border-blue-200 dark:border-blue-800/70',
    outline:
      'bg-transparent text-slate-600 dark:text-slate-400 border-slate-300 dark:border-slate-700',
  };

  const dotColors: Record<string, string> = {
    default: 'bg-slate-500',
    success: 'bg-emerald-500',
    warning: 'bg-amber-500',
    danger: 'bg-red-500',
    info: 'bg-blue-500',
    outline: 'bg-slate-400',
  };

  const sizes: Record<string, string> = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-1 text-xs',
  };

  return (
    <span
      className={`inline-flex items-center gap-1.5 font-medium rounded-full border ${variants[variant]} ${sizes[size]} ${className}`}
      {...props}
    >
      {dot && <span className={`w-1.5 h-1.5 rounded-full ${dotColors[variant]}`} />}
      {children}
    </span>
  );
};
