'use client'

import { useMemo, useState } from 'react'
import useSWR from 'swr'
import { Shell } from '@/components/shell'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Table, TBody, TD, THead, TH, TR } from '@/components/ui/table'
import type { Account, User } from '@/lib/types'

async function api<T>(path: string, init?: RequestInit) {
  const base = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000'
  const res = await fetch(`${base}${path}`, { ...init, headers: { 'content-type': 'application/json' } })
  if (!res.ok) throw new Error(await res.text())
  return (await res.json()) as T
}

const swrOptions = {
  dedupingInterval: 15000,
  revalidateOnFocus: false,
  revalidateOnReconnect: false,
  shouldRetryOnError: false,
}

const fetcher = <T,>(path: string) => api<T>(path)

export default function OltpPage() {
  const [busy, setBusy] = useState(false)

  const { data: users, mutate: mutateUsers } = useSWR<User[]>('/oltp/users', fetcher, swrOptions)
  const { data: accounts, mutate: mutateAccounts } = useSWR<Account[]>('/oltp/accounts', fetcher, swrOptions)

  const [newUser, setNewUser] = useState({ id: '', name: '', email: '' })
  const [newAccount, setNewAccount] = useState({ id: '', userId: '', accountNumber: '', accountType: 'Checking', name: '', balance: '0' })
  const [transfer, setTransfer] = useState({ fromAccountId: '', toAccountId: '', amount: '0', description: 'Transfer', category: 'Transfer' })

  const canCreateUser = useMemo(() => newUser.id && newUser.name && newUser.email, [newUser])
  const userList = users ?? []
  const accountList = accounts ?? []

  async function onCreateUser() {
    setBusy(true)
    try {
      await api('/oltp/users', { method: 'POST', body: JSON.stringify(newUser) })
      setNewUser({ id: '', name: '', email: '' })
      await mutateUsers()
    } finally {
      setBusy(false)
    }
  }

  async function onCreateAccount() {
    setBusy(true)
    try {
      await api('/oltp/accounts', {
        method: 'POST',
        body: JSON.stringify({
          ...newAccount,
          userId: newAccount.userId || null,
          balance: Number(newAccount.balance)
        })
      })
      setNewAccount({ id: '', userId: '', accountNumber: '', accountType: 'Checking', name: '', balance: '0' })
      await Promise.all([mutateAccounts(), mutateUsers()])
    } finally {
      setBusy(false)
    }
  }

  async function onTransfer() {
    setBusy(true)
    try {
      await api('/oltp/transfer', {
        method: 'POST',
        body: JSON.stringify({
          ...transfer,
          amount: Number(transfer.amount)
        })
      })
      await Promise.all([mutateAccounts(), mutateUsers()])
    } finally {
      setBusy(false)
    }
  }

  return (
    <Shell activeHref="/oltp">
      <div className="mb-6">
        <h1 className="text-2xl font-bold" style={{ color: '#0076d6' }}>Transaction Management</h1>
        <div className="text-sm text-zinc-600">Create users, accounts, and execute transfers</div>
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        <Card className="border-t-4 shadow-sm" style={{ borderTopColor: '#0076d6' }}>
          <CardHeader>
            <CardTitle style={{ color: '#0076d6' }}>Create User</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="grid gap-2">
              <Label>User ID</Label>
              <Input value={newUser.id} onChange={(e) => setNewUser({ ...newUser, id: e.target.value })} placeholder="u_001" />
            </div>
            <div className="grid gap-2">
              <Label>Name</Label>
              <Input value={newUser.name} onChange={(e) => setNewUser({ ...newUser, name: e.target.value })} placeholder="Ada" />
            </div>
            <div className="grid gap-2">
              <Label>Email</Label>
              <Input value={newUser.email} onChange={(e) => setNewUser({ ...newUser, email: e.target.value })} placeholder="ada@example.com" />
            </div>
            <Button disabled={!canCreateUser || busy} onClick={onCreateUser} className="shadow-sm" style={{ backgroundColor: '#0076d6', color: 'white', border: 'none' }}>
              Create User
            </Button>
          </CardContent>
        </Card>

        <Card className="border-t-4 shadow-sm" style={{ borderTopColor: '#0076d6' }}>
          <CardHeader>
            <CardTitle style={{ color: '#0076d6' }}>Create Account</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="grid gap-2">
              <Label>Account ID</Label>
              <Input value={newAccount.id} onChange={(e) => setNewAccount({ ...newAccount, id: e.target.value })} placeholder="a_001" />
            </div>
            <div className="grid gap-2">
              <Label>User ID (optional)</Label>
              <Input value={newAccount.userId} onChange={(e) => setNewAccount({ ...newAccount, userId: e.target.value })} placeholder="u_001" />
            </div>
            <div className="grid gap-2">
              <Label>Account Number</Label>
              <Input value={newAccount.accountNumber} onChange={(e) => setNewAccount({ ...newAccount, accountNumber: e.target.value })} placeholder="000123" />
            </div>
            <div className="grid gap-2">
              <Label>Name</Label>
              <Input value={newAccount.name} onChange={(e) => setNewAccount({ ...newAccount, name: e.target.value })} placeholder="Primary Checking" />
            </div>
            <div className="grid gap-2">
              <Label>Type</Label>
              <Input value={newAccount.accountType} onChange={(e) => setNewAccount({ ...newAccount, accountType: e.target.value })} placeholder="Checking" />
            </div>
            <div className="grid gap-2">
              <Label>Starting Balance</Label>
              <Input value={newAccount.balance} onChange={(e) => setNewAccount({ ...newAccount, balance: e.target.value })} placeholder="1000" />
            </div>
            <Button disabled={busy} onClick={onCreateAccount} className="shadow-sm" style={{ backgroundColor: '#0076d6', color: 'white', border: 'none' }}>
              Create Account
            </Button>
          </CardContent>
        </Card>
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <Card className="border-t-4 shadow-sm" style={{ borderTopColor: '#0076d6' }}>
          <CardHeader>
            <CardTitle style={{ color: '#0076d6' }}>Transfer</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="grid gap-2">
              <Label>From Account ID</Label>
              <Input value={transfer.fromAccountId} onChange={(e) => setTransfer({ ...transfer, fromAccountId: e.target.value })} placeholder="a_001" />
            </div>
            <div className="grid gap-2">
              <Label>To Account ID</Label>
              <Input value={transfer.toAccountId} onChange={(e) => setTransfer({ ...transfer, toAccountId: e.target.value })} placeholder="a_002" />
            </div>
            <div className="grid gap-2">
              <Label>Amount</Label>
              <Input value={transfer.amount} onChange={(e) => setTransfer({ ...transfer, amount: e.target.value })} placeholder="25.00" />
            </div>
            <Button disabled={busy} onClick={onTransfer} className="shadow-sm" style={{ backgroundColor: '#0076d6', color: 'white', border: 'none' }}>
              Post Transfer
            </Button>
          </CardContent>
        </Card>

        <Card className="border-t-4 shadow-sm" style={{ borderTopColor: '#0076d6' }}>
          <CardHeader>
            <CardTitle style={{ color: '#0076d6' }}>Accounts</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="rounded-md border">
              <div className="max-h-[420px] overflow-y-auto">
                <Table>
                  <THead>
                    <TR>
                      <TH>ID</TH>
                      <TH>Name</TH>
                      <TH className="text-right">Balance</TH>
                    </TR>
                  </THead>
                  <TBody>
                    {accountList.map((a: Account) => (
                      <TR key={a.id}>
                        <TD>{a.id}</TD>
                        <TD>{a.name}</TD>
                        <TD className="text-right">{a.balance.toFixed(2)}</TD>
                      </TR>
                    ))}
                  </TBody>
                </Table>
              </div>
            </div>
            <div className="mt-3 text-xs text-zinc-500">Users loaded: {userList.length}</div>
          </CardContent>
        </Card>
      </div>
    </Shell>
  )
}
