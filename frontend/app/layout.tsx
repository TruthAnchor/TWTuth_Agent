import type React from "react"
import type { Metadata } from "next"
import { GeistSans } from "geist/font/sans"
import { GeistMono } from "geist/font/mono"
import { Analytics } from "@vercel/analytics/next"
import "./globals.css"
import { SidebarProvider } from "@/components/sidebar-provider"
import { AppSidebar } from "@/components/app-sidebar"
import { TomoWalletProvider } from "@/contexts/tomo-wallet-context"
import { FallbackWalletProvider } from "@/contexts/fallback-wallet-context"
import { Suspense } from "react"

export const metadata: Metadata = {
  title: "TruthAnchor",
  description: "Transform your tweets into immutable states on the blockchain",
  generator: "v0.app",
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en">
      <body className={`font-sans ${GeistSans.variable} ${GeistMono.variable}`}>
        <Suspense fallback={<div>Loading...</div>}>
          <TomoWalletProvider>
            <FallbackWalletProvider>
              <SidebarProvider>
                <div className="flex h-screen">
                  <AppSidebar />
                  <main className="flex-1 overflow-auto">{children}</main>
                </div>
              </SidebarProvider>
            </FallbackWalletProvider>
          </TomoWalletProvider>
        </Suspense>
        <Analytics />
      </body>
    </html>
  )
}
