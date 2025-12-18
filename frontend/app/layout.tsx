import './globals.css'
import type { Metadata } from 'next'
import { Theme } from '@radix-ui/themes'
import '@radix-ui/themes/styles.css'

export const metadata: Metadata = {
  title: 'Fabric Banking Demo',
  description: 'OLTP, OLTAP, OLAP demo on Microsoft Fabric'
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <Theme appearance="light" accentColor="gray" radius="large">
          {children}
        </Theme>
      </body>
    </html>
  )
}
