"use client"

import { useTomoWallet } from "@/contexts/tomo-wallet-context"
import { useFallbackWallet } from "@/contexts/fallback-wallet-context"
import { Wallet, LogOut, AlertCircle, ExternalLink, Loader2, CheckCircle, AlertTriangle } from "lucide-react"
import { StylizedButton } from "@/components/ui/stylized-button"

export function WalletConnect() {
  const tomoWallet = useTomoWallet()
  const fallbackWallet = useFallbackWallet()

  // Use Tomo wallet if connected, otherwise use fallback
  const wallet = tomoWallet.isConnected ? tomoWallet : fallbackWallet

  const formatAddress = (addr: string | null) => {
    if (!addr) return ""
    return `${addr.substring(0, 6)}...${addr.substring(addr.length - 4)}`
  }

  const handleConnect = async () => {
    console.log("Wallet connect button clicked")

    // Always try Tomo first
    try {
      console.log("Attempting Tomo EVM Kit connection...")
      await tomoWallet.connectWallet()
    } catch (error) {
      console.warn("Tomo connection failed, trying fallback:", error)

      // Only try fallback if Tomo completely fails
      try {
        await fallbackWallet.connectWallet()
      } catch (fallbackError) {
        console.error("Both Tomo and fallback failed:", fallbackError)
      }
    }
  }

  // Show connection status
  if (wallet.isConnected && wallet.address) {
    const isTomoConnected = tomoWallet.isConnected
    const showChainWarning = isTomoConnected && !tomoWallet.isCorrectChain

    return (
      <div className="flex flex-col gap-2">
        <div className="flex items-center gap-2 bg-background/30 border border-primary/10 rounded-md px-3 py-1.5 w-full">
          <CheckCircle className="w-3 h-3 text-green-500/80" />
          <span className="text-xs font-mono truncate">{formatAddress(wallet.address)}</span>
          <span className="text-xs text-muted-foreground px-1.5 py-0.5 bg-muted/30 rounded">
            {isTomoConnected ? "Tomo" : "Web3"}
          </span>
        </div>
        <div className="flex items-center gap-2 w-full">
          <a
            href={`https://filscan.io/en/address/${wallet.address}`}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center justify-center px-3 py-1.5 bg-background/30 border border-primary/10 rounded-md text-xs hover:bg-background/50 transition-colors"
            title="View on Filecoin Explorer"
          >
            Explorer <ExternalLink className="w-3 h-3 ml-1" />
          </a>
          <StylizedButton
            variant="outline"
            size="sm"
            onClick={wallet.disconnectWallet}
            iconRight={<LogOut className="w-3.5 h-3.5" />}
            withIcon={true}
            className="flex-1 group"
          >
            Disconnect
          </StylizedButton>
        </div>

        {/* Chain warning for Tomo wallet */}
        {showChainWarning && (
          <div className="flex items-center gap-2 text-yellow-400/80 text-xs bg-yellow-500/5 border border-yellow-500/10 rounded-md px-3 py-1.5">
            <AlertTriangle className="w-3.5 h-3.5" />
            <span>Wrong network. </span>
            <button
              onClick={tomoWallet.switchToStoryChain}
              disabled={tomoWallet.isLoading}
              className="text-xs underline hover:no-underline"
            >
              Switch to Filecoin
            </button>
          </div>
        )}
      </div>
    )
  }

  // Show loading state
  if (wallet.isLoading) {
    return (
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 bg-background/30 border border-primary/10 rounded-md px-3 py-1.5">
          <Loader2 className="w-3.5 h-3.5 animate-spin text-primary/70" />
          <span className="text-xs">Connecting...</span>
        </div>
      </div>
    )
  }

  // Show error state
  if (tomoWallet.error || fallbackWallet.error) {
    return (
      <div className="flex flex-col gap-2">
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-2 text-red-400/80 text-xs bg-red-500/5 border border-red-500/10 rounded-md px-3 py-1.5">
            <AlertCircle className="w-3.5 h-3.5" />
            <span>{tomoWallet.error || fallbackWallet.error}</span>
          </div>
          <StylizedButton
            variant="outline"
            size="sm"
            onClick={handleConnect}
            iconRight={<Wallet className="w-3.5 h-3.5" />}
          >
            Retry
          </StylizedButton>
        </div>
      </div>
    )
  }

  // Show connect button
  return (
    <div className="flex items-center">
      <StylizedButton
        variant="primary"
        size="default"
        onClick={handleConnect}
        iconRight={<Wallet className="w-4 h-4" />}
        withIcon={true}
        className="w-full group"
      >
        Connect Wallet
      </StylizedButton>
    </div>
  )
}
