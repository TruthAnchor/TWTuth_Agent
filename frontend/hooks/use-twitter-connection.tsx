"use client"

import { useState, useEffect } from "react"

// Helper functions for Twitter OAuth
function randomString(len = 50) {
  const arr = new Uint8Array(len)
  if (typeof window !== "undefined") {
    window.crypto.getRandomValues(arr)
    return Array.from(arr)
      .map((b) => ("0" + b.toString(16)).slice(-2))
      .join("")
  }
  return Math.random().toString(36).substring(2, len)
}

async function sha256Base64url(str: string) {
  if (typeof window !== "undefined") {
    const buf = await window.crypto.subtle.digest("SHA-256", new TextEncoder().encode(str))
    const b64 = btoa(String.fromCharCode(...new Uint8Array(buf)))
    return b64.replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "")
  }
  return ""
}

export function useTwitterConnection() {
  const [isConnected, setIsConnected] = useState(false)
  const [handle, setHandle] = useState<string | undefined>(undefined)
  const [userId, setUserId] = useState<string | undefined>(undefined)
  const [name, setName] = useState<string | undefined>(undefined)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [popup, setPopup] = useState<Window | null>(null)

  // Twitter OAuth configuration
  const clientId = process.env.NEXT_PUBLIC_TWITTER_CLIENT_ID || ""
  const baseUrl = process.env.NEXT_PUBLIC_BASE_URL || (typeof window !== "undefined" ? window.location.origin : "")
  const redirectUri = `${baseUrl}/twitter-callback`
  const scope = "tweet.read users.read offline.access"

  useEffect(() => {
    // Check if we have Twitter credentials in localStorage
    if (typeof window !== "undefined") {
      const storedHandle = localStorage.getItem("twitter_handle")
      const storedId = localStorage.getItem("twitter_id")
      const storedName = localStorage.getItem("twitter_name")

      if (storedHandle) {
        setIsConnected(true)
        setHandle(storedHandle)
        setUserId(storedId || undefined)
        setName(storedName || undefined)
      }
    }
  }, [])

  // Listen for messages from the popup
  useEffect(() => {
    if (typeof window === "undefined") return

    const handleMessage = async (evt: MessageEvent) => {
      if (evt.origin !== window.location.origin) return

      // Check if this is our Twitter auth message
      if (evt.data && evt.data.type === "TWITTER_AUTH_SUCCESS") {
        try {
          setIsLoading(true)
          setError(null)

          // Get the user data from the message
          const { username, id, name } = evt.data

          // Store the user data in localStorage
          localStorage.setItem("twitter_handle", username)
          if (id) localStorage.setItem("twitter_id", id)
          if (name) localStorage.setItem("twitter_name", name)

          // Update state
          setIsConnected(true)
          setHandle(username)
          setUserId(id)
          setName(name)

          // Close the popup if it's still open
          if (popup && !popup.closed) {
            popup.close()
          }
        } catch (err) {
          console.error("Error processing Twitter callback:", err)
          setError(err instanceof Error ? err.message : "Failed to connect Twitter")
        } finally {
          setIsLoading(false)
        }
      }
    }

    window.addEventListener("message", handleMessage)
    return () => window.removeEventListener("message", handleMessage)
  }, [popup])

  // Check if popup is closed without completing auth
  useEffect(() => {
    if (!popup || isConnected) return

    const checkPopup = setInterval(() => {
      if (popup.closed) {
        clearInterval(checkPopup)
        if (!isConnected && isLoading) {
          setIsLoading(false)
          setError("Authentication was canceled")
        }
      }
    }, 500)

    return () => clearInterval(checkPopup)
  }, [popup, isConnected, isLoading])

  const connect = async () => {
    try {
      setIsLoading(true)
      setError(null)

      if (!clientId) {
        throw new Error("Twitter Client ID not configured")
      }

      console.log("[v0] Twitter connect - Configuration:", {
        clientIdLength: clientId.length,
        baseUrl,
        redirectUri,
      })

      // 1) build PKCE verifier & challenge
      const verifier = randomString()
      const challenge = await sha256Base64url(verifier)

      // Store both the verifier and the exact redirect URI used
      localStorage.setItem("pkce_verifier", verifier)
      localStorage.setItem("twitter_redirect_uri", redirectUri)

      // 2) open popup to Twitter
      const authURL = new URL("https://twitter.com/i/oauth2/authorize")
      authURL.search = new URLSearchParams({
        response_type: "code",
        client_id: clientId,
        redirect_uri: redirectUri,
        scope: scope,
        state: "story_graph_state", // CSRF token
        code_challenge: challenge,
        code_challenge_method: "S256",
      }).toString()

      console.log("[v0] Twitter connect - Opening auth URL:", authURL.toString())

      const newPopup = window.open(authURL.toString(), "twitter_login", "width=600,height=700")
      setPopup(newPopup)

      // If popup is blocked, provide a fallback
      if (!newPopup || newPopup.closed || typeof newPopup.closed === "undefined") {
        setError("Popup was blocked. Please allow popups for this site.")
        setIsLoading(false)
      }
    } catch (error) {
      console.error("Error connecting Twitter:", error)
      setError(error instanceof Error ? error.message : "Failed to connect Twitter")
      setIsLoading(false)
    }
  }

  const disconnect = () => {
    localStorage.removeItem("twitter_handle")
    localStorage.removeItem("twitter_id")
    localStorage.removeItem("twitter_name")
    localStorage.removeItem("pkce_verifier")
    localStorage.removeItem("twitter_redirect_uri")
    setIsConnected(false)
    setHandle(undefined)
    setUserId(undefined)
    setName(undefined)
    setError(null)
  }

  return {
    isConnected,
    handle,
    userId,
    name,
    connect,
    disconnect,
    isLoading,
    error,
  }
}
