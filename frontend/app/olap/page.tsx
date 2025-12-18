'use client'

import { useState } from 'react'
import useSWR from 'swr'
import { Shell } from '@/components/shell'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Table, TBody, TD, THead, TH, TR } from '@/components/ui/table'
import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, ResponsiveContainer, XAxis, YAxis, Tooltip, Legend, CartesianGrid } from 'recharts'
import { CHART_COLORS, SERIES_COLORS } from '@/lib/colors'

type Row = { category: string; amount: number; transactions: number }
type SpendResponse = { from: string; to: string; rows: Row[] }

// Colors come from shared palette

const swrOptions = {
  dedupingInterval: 15000,
  revalidateOnFocus: false,
  revalidateOnReconnect: false,
  revalidateOnMount: true,
  refreshInterval: 0,
  shouldRetryOnError: false,
}

async function getSpend(params: { from?: string; to?: string }) {
  const base = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000'
  const url = new URL('/olap/spend', base)
  if (params.from) url.searchParams.set('from', params.from)
  if (params.to) url.searchParams.set('to', params.to)
  const res = await fetch(url.toString())
  if (!res.ok) throw new Error(await res.text())
  return (await res.json()) as SpendResponse
}

export default function OlapPage() {
  // Set default date range: last 90 days
  const today = new Date().toISOString().split('T')[0]
  const ninetyDaysAgo = new Date(Date.now() - 90 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
  
  const [from, setFrom] = useState(ninetyDaysAgo)
  const [to, setTo] = useState(today)

  const key = ['/olap/spend', from, to] as const
  const { data, isValidating, error, mutate } = useSWR(
    key,
    ([, f, t]) =>
      getSpend({
        from: f as string | undefined,
        to: t as string | undefined,
      }),
    swrOptions
  )


  const rows = data?.rows ?? []
  const chartData = rows.map((r: Row) => ({
    name: r.category || '(none)',
    amount: r.amount,
    transactions: r.transactions,
  }))

  const totalAmount = rows.reduce((sum, r) => sum + r.amount, 0)
  const totalTxns = rows.reduce((sum, r) => sum + r.transactions, 0)

  return (
    <Shell activeHref="/olap">
      <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-blue-600">Analytics & Insights</h1>
          <div className="text-sm text-zinc-600">Historical trends and category breakdowns</div>
        </div>
        <div className="flex gap-2">
          <div className="grid gap-1">
            <Label className="text-xs text-zinc-600">From</Label>
            <Input type="date" value={from} onChange={(e) => setFrom(e.target.value)} className="border-zinc-300" />
          </div>
          <div className="grid gap-1">
            <Label className="text-xs text-zinc-600">To</Label>
            <Input type="date" value={to} onChange={(e) => setTo(e.target.value)} className="border-zinc-300" />
          </div>
          <div className="flex items-end">
            <Button 
              variant="secondary" 
              onClick={() => mutate()} 
              disabled={isValidating}
              className="shadow-sm bg-blue-600 text-white hover:bg-blue-700"
            >
              {isValidating ? 'Loading...' : 'Analyze'}
            </Button>
          </div>
        </div>
      </div>

      {error && (
        <div className="mt-4 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800">
          Failed to load analytics. {isValidating ? 'Retrying...' : 'Click Analyze to try again.'}
        </div>
      )}

      {isValidating && !data && (
        <div className="mt-4 flex items-center justify-center rounded-lg bg-blue-50 p-8">
          <div className="text-center">
            <div className="text-sm text-blue-700">Analyzing transactions...</div>
          </div>
        </div>
      )}

      {data && (
        <div>
          <div className="mt-6 grid gap-4 md:grid-cols-2">
            <Card className="border-t-4 shadow-sm" style={{ borderTopColor: SERIES_COLORS.primary }}>
          <CardHeader>
            <CardTitle className="text-sm text-zinc-600">Total Spend</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-blue-600">${totalAmount.toFixed(2)}</div>
            <div className="mt-1 text-xs text-zinc-500">
              {data?.from ?? '--'} → {data?.to ?? '--'}
            </div>
          </CardContent>
        </Card>
        <Card className="border-t-4 shadow-sm" style={{ borderTopColor: SERIES_COLORS.secondary }}>
          <CardHeader>
            <CardTitle className="text-sm text-zinc-600">Total Transactions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-green-600">{totalTxns}</div>
            <div className="mt-1 text-xs text-zinc-500">
              Across {rows.length} categories
            </div>
          </CardContent>
        </Card>
          </div>

          <div className="mt-6 grid gap-4 md:grid-cols-2">
            <Card className="shadow-sm">
            <CardHeader>
            <CardTitle className="text-blue-600">Spend by Category</CardTitle>
          </CardHeader>
          <CardContent>
            {chartData.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip />
                  <Bar dataKey="amount" radius={[8, 8, 0, 0]}>
                    {chartData.map((_, index: number) => (
                      <Cell key={`amount-cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex h-[300px] items-center justify-center text-sm text-zinc-400">No data available</div>
            )}
          </CardContent>
        </Card>

        <Card className="shadow-sm">
          <CardHeader>
            <CardTitle className="text-blue-600">Transaction Volume</CardTitle>
          </CardHeader>
          <CardContent>
            {chartData.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip />
                  <Bar dataKey="transactions" fill={SERIES_COLORS.secondary} radius={[8, 8, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex h-[300px] items-center justify-center text-sm text-zinc-400">No data available</div>
            )}
          </CardContent>
        </Card>
          </div>

          <Card className="mt-4 shadow-sm">
            <CardHeader>
              <CardTitle className="text-blue-600">Detailed Breakdown</CardTitle>
            </CardHeader>
            <CardContent>
          <Table>
            <THead>
              <TR>
                <TH>Category</TH>
                <TH className="text-right">Transactions</TH>
                <TH className="text-right">Amount</TH>
                <TH className="text-right">Avg/Txn</TH>
              </TR>
            </THead>
            <TBody>
              {rows.map((r: Row) => (
                <TR key={r.category}>
                  <TD className="font-medium">{r.category || '(none)'}</TD>
                  <TD className="text-right">{r.transactions}</TD>
                  <TD className="text-right">${r.amount.toFixed(2)}</TD>
                  <TD className="text-right text-zinc-600">${(r.transactions ? r.amount / r.transactions : 0).toFixed(2)}</TD>
                </TR>
              ))}
            </TBody>
          </Table>
            </CardContent>
          </Card>
        </div>
      )}
    </Shell>
  )
}
