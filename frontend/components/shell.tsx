import { Nav } from '@/components/nav'

export function Shell({ activeHref, children }: { activeHref: string; children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-zinc-50">
      <header className="border-b border-[#0076d6] bg-[#0076d6] text-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
          <div className="text-lg font-semibold">Fabric Banking Demo</div>
          <Nav activeHref={activeHref} />
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-6">{children}</main>
    </div>
  )
}
