import Link from 'next/link'
import { cn } from '@/lib/cn'

const links = [
  { href: '/', label: 'Overview', activeClass: 'bg-white/20', hoverClass: 'hover:bg-white/10' },
  { href: '/oltp', label: 'Transaction Mgmt', activeClass: 'bg-white/20', hoverClass: 'hover:bg-white/10' },
  { href: '/oltap', label: 'Real-Time', activeClass: 'bg-white/20', hoverClass: 'hover:bg-white/10' },
  { href: '/olap', label: 'Analytics', activeClass: 'bg-white/20', hoverClass: 'hover:bg-white/10' },
  { href: '/agent', label: 'AI Assistant', activeClass: 'bg-white/20', hoverClass: 'hover:bg-white/10' }
]

export function Nav({ activeHref }: { activeHref: string }) {
  return (
    <nav className="flex items-center gap-1">
      {links.map((l) => (
        <Link
          key={l.href}
          href={l.href}
          className={cn(
            'rounded-md px-3 py-2 text-sm transition-colors text-white/85',
            activeHref === l.href ? `${l.activeClass} font-semibold text-white` : l.hoverClass
          )}
        >
          {l.label}
        </Link>
      ))}
    </nav>
  )
}
