import * as React from 'react'
import { cn } from '@/lib/cn'

export function Input({ className, ...props }: React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={cn(
        'h-10 w-full rounded-md border px-3 text-sm outline-none focus:ring-2 focus:ring-black/20',
        className
      )}
      {...props}
    />
  )
}
