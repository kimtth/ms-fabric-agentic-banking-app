import * as React from 'react'
import { cn } from '@/lib/cn'

export function Label({ className, ...props }: React.LabelHTMLAttributes<HTMLLabelElement>) {
  return <label className={cn('text-sm text-zinc-700', className)} {...props} />
}
