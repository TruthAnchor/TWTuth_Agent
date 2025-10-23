"use client"

import Link from "next/link"
import { Home, MessageSquare, Info, Map, Users, Compass } from "lucide-react"
import { Sidebar, SidebarContent, SidebarHeader, SidebarFooter } from "@/components/sidebar-provider"
import { WalletConnect } from "@/components/wallet-connect"
import { TwitterConnect } from "@/components/twitter-connect"

export function AppSidebar() {
  return (
    <Sidebar>
      <SidebarHeader className="border-b border-sidebar-border pb-4">
        <div className="flex items-center justify-center mb-4">
          <h1 className="text-xl font-bold tracking-tight neon-glow">Truth Anchor</h1>
        </div>

        <div className="space-y-3 overflow-hidden">
          <WalletConnect />
          <TwitterConnect />
        </div>
      </SidebarHeader>

      <SidebarContent className="py-4">
        <nav className="space-y-1 px-2">
          <Link
            href="/"
            className="flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
          >
            <Home size={16} />
            <span>Home</span>
          </Link>
          <Link
            href="/explore"
            className="flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
          >
            <Compass size={16} />
            <span>Explore</span>
          </Link>
          <Link
            href="/my-tweets"
            className="flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
          >
            <MessageSquare size={16} />
            <span>My Tweets</span>
          </Link>
          <Link
            href="/about"
            className="flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
          >
            <Info size={16} />
            <span>About</span>
          </Link>
          <Link
            href="/roadmap"
            className="flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
          >
            <Map size={16} />
            <span>Roadmap</span>
          </Link>
          <Link
            href="/community"
            className="flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
          >
            <Users size={16} />
            <span>Community</span>
          </Link>
        </nav>
      </SidebarContent>

      <SidebarFooter className="border-t border-sidebar-border pt-4">
        <div className="px-2 text-xs text-muted-foreground">
          <p>© 2025 Truth Anchor</p>
        </div>
      </SidebarFooter>
    </Sidebar>
  )
}
