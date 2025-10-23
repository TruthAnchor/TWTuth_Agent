"use client"

import { Twitter, LogOut, AlertCircle, Loader2 } from "lucide-react"
import { useTwitterConnection } from "@/hooks/use-twitter-connection"
import { StylizedButton } from "@/components/ui/stylized-button"
import { Alert, AlertDescription } from "@/components/ui/alert"

export function TwitterConnect() {
  const { isConnected, handle, connect, disconnect, isLoading, error } = useTwitterConnection()

  if (isLoading) {
    return (
      <StylizedButton
        variant="outline"
        className="w-full"
        disabled
        iconRight={<Loader2 className="w-4 h-4 animate-spin" />}
        withIcon={true}
      >
        Connecting...
      </StylizedButton>
    )
  }

  if (error) {
    return (
      <div className="space-y-2">
        <Alert variant="destructive" className="py-2">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription className="text-xs">{error}</AlertDescription>
        </Alert>
        <StylizedButton
          variant="outline"
          className="w-full"
          onClick={connect}
          iconRight={<Twitter className="w-4 h-4" />}
          withIcon={true}
        >
          Retry Twitter
        </StylizedButton>
      </div>
    )
  }

  if (isConnected && handle) {
    return (
      <div className="flex flex-col gap-2">
        <div className="flex items-center gap-2 bg-background/30 border border-primary/10 rounded-md px-3 py-1.5 w-full">
          <Twitter className="w-3.5 h-3.5 text-primary/70" />
          <span className="text-xs font-medium truncate">@{handle}</span>
        </div>
        <StylizedButton
          variant="outline"
          size="sm"
          onClick={disconnect}
          iconRight={<LogOut className="w-3.5 h-3.5" />}
          withIcon={true}
          className="w-full group"
        >
          Disconnect
        </StylizedButton>
      </div>
    )
  }

  return (
    <StylizedButton
      variant="primary"
      className="w-full group"
      onClick={connect}
      iconRight={<Twitter className="w-4 h-4" />}
      withIcon={true}
      disabled={!process.env.NEXT_PUBLIC_TWITTER_CLIENT_ID}
      title={!process.env.NEXT_PUBLIC_TWITTER_CLIENT_ID ? "Twitter Client ID not configured" : "Connect Twitter"}
    >
      Connect Twitter
      {!process.env.NEXT_PUBLIC_TWITTER_CLIENT_ID && <span className="text-xs opacity-70"> (Not Configured)</span>}
    </StylizedButton>
  )
}
