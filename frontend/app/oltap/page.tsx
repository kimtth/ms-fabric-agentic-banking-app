'use client'

import useSWR from 'swr'
import { Shell } from '@/components/shell'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { BarChart, Bar, PieChart, Pie, Cell, ResponsiveContainer, XAxis, YAxis, Tooltip, Legend } from 'recharts'
import { CHART_COLORS, SERIES_COLORS } from '@/lib/colors'

type Summary = {
  windowMinutes: number
  transactions: number
  totalAmount: number
  topCategories: { category: string; amount: number }[]
}

// Colors come from shared palette

const swrOptions = {
  dedupingInterval: 15000,
  revalidateOnFocus: false,
  revalidateOnReconnect: false,
  revalidateOnMount: true,
  refreshInterval: 0,
  shouldRetryOnError: true,
  errorRetryCount: 3,
  errorRetryInterval: 1000,
}

const fetcher = async <T,>(path: string) => {
  const base = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000'
  const res = await fetch(`${base}${path}`)
  if (!res.ok) throw new Error(await res.text())
  return (await res.json()) as T
}

export default function OltapPage() {
  const { data, isValidating, error, mutate } = useSWR<Summary>('/oltap/summary', fetcher, swrOptions)

  const chartData = (data?.topCategories ?? []).map((c: Summary['topCategories'][number]) => ({
    name: c.category || '(none)',
    value: c.amount,
  }))

  return (
    <Shell activeHref="/oltap">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-blue-600">Real-Time Dashboard</h1>
          <div className="text-sm text-zinc-600">Live operational metrics and transaction activity</div>
        </div>
        <Button 
          variant="secondary" 
          onClick={() => mutate()} 
          disabled={isValidating} 
          className="shadow-sm bg-blue-600 text-white hover:bg-blue-700"
        >
          {isValidating ? 'Loading...' : 'Refresh'}
        </Button>
      </div>

      {error && (
        <div className="mt-4 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800">
          Failed to load data. {isValidating ? 'Retrying...' : 'Click Refresh to try again.'}
        </div>
      )}

      {isValidating && !data && (
        <div className="mt-4 flex items-center justify-center rounded-lg bg-blue-50 p-8">
          <div className="text-center">
            <div className="text-sm text-blue-700">Loading real-time data...</div>
          </div>
        </div>
      )}

      {data && (
        <>
          <div className="mt-6 grid gap-4 md:grid-cols-3">
            <Card className="border-t-4 shadow-sm transition-shadow hover:shadow-md" style={{ borderTopColor: SERIES_COLORS.primary }}>
              <CardHeader>
                <CardTitle className="text-sm text-zinc-600">Time Window</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-blue-600">{data?.windowMinutes ?? '--'}<span className="text-lg">m</span></div>
              </CardContent>
            </Card>
            <Card className="border-t-4 shadow-sm transition-shadow hover:shadow-md" style={{ borderTopColor: SERIES_COLORS.secondary }}>
              <CardHeader>
                <CardTitle className="text-sm text-zinc-600">Active Transactions</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-green-600">{data?.transactions ?? '--'}</div>
              </CardContent>
            </Card>
            <Card className="border-t-4 shadow-sm transition-shadow hover:shadow-md" style={{ borderTopColor: SERIES_COLORS.accent }}>
              <CardHeader>
                <CardTitle className="text-sm text-zinc-600">Total Volume</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-amber-600">${data ? data.totalAmount.toFixed(2) : '--'}</div>
              </CardContent>
            </Card>
          </div>

          <div className="mt-6 grid gap-4 md:grid-cols-2">
            <Card className="shadow-sm">
                <CardHeader>
                <CardTitle className="text-blue-600">Category Distribution</CardTitle>
              </CardHeader>
              <CardContent>
                {chartData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                        data={chartData}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                        outerRadius={80}
                        fill="#8884d8"
                        dataKey="value"
                      >
                        {chartData.map((entry: { name: string; value: number }, index: number) => (
                          <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="flex h-[300px] items-center justify-center text-sm text-zinc-400">No data available</div>
                )}
              </CardContent>
            </Card>

            <Card className="shadow-sm">
              <CardHeader>
                <CardTitle className="text-blue-600">Top Categories</CardTitle>
              </CardHeader>
              <CardContent>
                {chartData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={chartData}>
                      <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                      <YAxis tick={{ fontSize: 12 }} />
                      <Tooltip />
                      <Bar dataKey="value" radius={[8, 8, 0, 0]}>
                        {chartData.map((_, index: number) => (
                          <Cell key={`bar-cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="flex h-[300px] items-center justify-center text-sm text-zinc-400">No data available</div>
                )}
              </CardContent>
            </Card>
          </div>
        </>
      )}
    </Shell>
  )
}
