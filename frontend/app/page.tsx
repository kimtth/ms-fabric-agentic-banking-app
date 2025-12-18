"use client"

import Link from 'next/link'
import useSWR from 'swr'
import { Shell } from '@/components/shell'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { CHART_COLORS, SERIES_COLORS } from '@/lib/colors'

type Summary = {
  windowMinutes: number
  transactions: number
  totalAmount: number
  topCategories: { category: string; amount: number }[]
}

const fetcher = async <T,>(path: string) => {
  const base = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000'
  const res = await fetch(`${base}${path}`)
  if (!res.ok) throw new Error(await res.text())
  return (await res.json()) as T
}

export default function Page() {
  const { data } = useSWR<Summary>('/oltap/summary', fetcher, {
    dedupingInterval: 15000,
    revalidateOnFocus: false,
    revalidateOnReconnect: false,
  })

  const topCats = (data?.topCategories ?? []).slice(0, 5)
  return (
    <Shell activeHref="/">
      <div className="mb-6 text-center">
        <h1 className="text-3xl font-bold" style={{ color: '#000000ff' }}>Banking Platform</h1>
        <p className="mt-2 text-zinc-600">Modern data platform with transactional, real-time, and analytical capabilities</p>
      </div>
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <Card className="border-t-4 shadow-sm transition-all hover:shadow-lg" style={{ borderTopColor: '#4f74a5' }}>
          <CardHeader>
            <CardTitle style={{ color: '#0076d6d6' }}>Transaction Management</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-sm text-zinc-700 mb-4">Create users, accounts and execute transfers with ACID guarantees.</div>
            <Link 
              className="inline-block text-sm font-medium hover:underline" 
              style={{ color: '#0076d6' }}
              href="/oltp"
            >
              Open OLTP →
            </Link>
          </CardContent>
        </Card>

        <Card className="border-t-4 shadow-sm transition-all hover:shadow-lg" style={{ borderTopColor: '#4f74a5' }}>
          <CardHeader>
            <CardTitle style={{ color: '#0076d6' }}>Real-Time Dashboard</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-sm text-zinc-700 mb-4">Live operational metrics and transaction activity monitoring.</div>
            <Link 
              className="inline-block text-sm font-medium hover:underline" 
              style={{ color: '#0076d6' }}
              href="/oltap"
            >
              Open OLTAP →
            </Link>
          </CardContent>
        </Card>

        <Card className="border-t-4 shadow-sm transition-all hover:shadow-lg" style={{ borderTopColor: '#4f74a5' }}>
          <CardHeader>
            <CardTitle style={{ color: '#0076d6' }}>Analytics & Insights</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-sm text-zinc-700 mb-4">Historical trends and category breakdowns for deep analysis.</div>
            <Link 
              className="inline-block text-sm font-medium hover:underline" 
              style={{ color: '#0076d6' }}
              href="/olap"
            >
              Open OLAP →
            </Link>
          </CardContent>
        </Card>

        <Card className="border-t-4 shadow-sm transition-all hover:shadow-lg" style={{ borderTopColor: '#4f74a5' }}>
          <CardHeader>
            <CardTitle style={{ color: '#0076d6' }}>AI Assistant</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-sm text-zinc-700 mb-4">Chat with AI to explore and analyze your banking data.</div>
            <Link 
              className="inline-block text-sm font-medium hover:underline" 
              style={{ color: '#0076d6' }}
              href="/agent"
            >
              Open Agent →
            </Link>
          </CardContent>
        </Card>
      </div>

      {/* Quick glance metrics */}
      <div className="mt-8 grid gap-4 md:grid-cols-3">
        <Card className="border-t-4" style={{ borderTopColor: SERIES_COLORS.primary }}>
          <CardHeader>
            <CardTitle className="text-sm text-zinc-600">Window</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-blue-600">{data?.windowMinutes ?? '--'}<span className="text-lg">m</span></div>
            <div className="mt-1 text-xs text-zinc-500">Real-time summary window</div>
          </CardContent>
        </Card>
        <Card className="border-t-4" style={{ borderTopColor: SERIES_COLORS.secondary }}>
          <CardHeader>
            <CardTitle className="text-sm text-zinc-600">Transactions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-green-600">{data?.transactions ?? '--'}</div>
            <div className="mt-1 text-xs text-zinc-500">Processed in the window</div>
          </CardContent>
        </Card>
        <Card className="border-t-4" style={{ borderTopColor: SERIES_COLORS.accent }}>
          <CardHeader>
            <CardTitle className="text-sm text-zinc-600">Total Volume</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-amber-600">${data ? data.totalAmount.toFixed(2) : '--'}</div>
            <div className="mt-1 text-xs text-zinc-500">Across all categories</div>
          </CardContent>
        </Card>
      </div>

      {/* Top categories snapshot */}
      <div className="mt-6">
        <Card className="shadow-sm">
          <CardHeader>
            <CardTitle className="text-blue-600">Top Categories</CardTitle>
          </CardHeader>
          <CardContent>
            {topCats.length > 0 ? (
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {topCats.map((c, i) => (
                  <div key={c.category + i} className="flex items-center justify-between rounded-md border p-3">
                    <div className="flex items-center gap-3">
                      <span
                        className="inline-block h-3 w-3 rounded-full"
                        style={{ backgroundColor: CHART_COLORS[i % CHART_COLORS.length] }}
                        aria-hidden
                      />
                      <div className="font-medium">{c.category || '(none)'}</div>
                    </div>
                    <div className="text-sm tabular-nums">${c.amount.toFixed(2)}</div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-sm text-zinc-500">No recent categories available.</div>
            )}
          </CardContent>
        </Card>
      </div>
    </Shell>
  )
}
