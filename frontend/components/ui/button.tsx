import * as React from 'react'
import { cn } from '@/lib/cn'

type Props = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: 'primary' | 'secondary' | 'ghost'
}

export function Button({ className, variant = 'primary', ...props }: Props) {
  return (
    <button
      className={cn(
        'inline-flex items-center justify-center rounded-md px-3 py-2 text-sm font-medium transition-colors disabled:opacity-50',
        variant === 'primary' && 'bg-black text-white hover:bg-black/90',
        variant === 'secondary' && 'bg-zinc-100 text-zinc-900 hover:bg-zinc-200',
        variant === 'ghost' && 'hover:bg-zinc-100',
        className
      )}
      {...props}
    />
  )
}
