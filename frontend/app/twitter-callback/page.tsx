"use client"

import { useEffect, useState } from "react"
import { useSearchParams } from "next/navigation"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Loader2, CheckCircle, AlertCircle } from "lucide-react"

export default function TwitterCallbackPage() {
  const searchParams = useSearchParams()
  const [status, setStatus] = useState<"loading" | "success" | "error">("loading")
  const [message, setMessage] = useState("Processing Twitter authentication...")

  useEffect(() => {
    const handleCallback = async () => {
      try {
        const code = searchParams.get("code")
        const state = searchParams.get("state")
        const error = searchParams.get("error")

        if (error) {
          throw new Error(`Twitter authentication failed: ${error}`)
        }

        if (!code) {
          throw new Error("No authorization code received")
        }

        console.log("Twitter callback - Received code:", code)

        // Get the stored PKCE verifier and redirect URI
        const verifier = localStorage.getItem("pkce_verifier")
        const redirectUri = localStorage.getItem("twitter_redirect_uri")

        if (!verifier) {
          throw new Error("PKCE verifier not found. Please try connecting again.")
        }

        console.log("Twitter callback - Using stored verifier and redirect URI")

        // Exchange the code for an access token via our API route
        const response = await fetch("/api/twitter/exchange", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            code,
            codeVerifier: verifier,
            redirectUri: redirectUri,
          }),
        })

        const responseText = await response.text()
        console.log("Twitter callback - Exchange response:", {
          status: response.status,
          body: responseText,
        })

        if (!response.ok) {
          let errorData
          try {
            errorData = JSON.parse(responseText)
          } catch {
            errorData = { error: responseText }
          }
          throw new Error(errorData.error || "Failed to exchange authorization code")
        }

        const data = JSON.parse(responseText)
        console.log("Twitter callback - User data:", data)

        // Send the user data back to the parent window
        if (window.opener) {
          window.opener.postMessage(
            {
              type: "TWITTER_AUTH_SUCCESS",
              username: data.username,
              id: data.id,
              name: data.name,
            },
            window.location.origin,
          )
        }

        setStatus("success")
        setMessage("Successfully connected Twitter account!")

        // Close the popup after a short delay
        setTimeout(() => {
          window.close()
        }, 2000)
      } catch (error) {
        console.error("Twitter callback error:", error)
        setStatus("error")
        setMessage(error instanceof Error ? error.message : "Authentication failed")
      }
    }

    handleCallback()
  }, [searchParams])

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            {status === "loading" && <Loader2 className="w-5 h-5 animate-spin" />}
            {status === "success" && <CheckCircle className="w-5 h-5 text-green-500" />}
            {status === "error" && <AlertCircle className="w-5 h-5 text-red-500" />}
            Twitter Authentication
          </CardTitle>
          <CardDescription>
            {status === "loading" && "Processing your authentication..."}
            {status === "success" && "Authentication successful!"}
            {status === "error" && "Authentication failed"}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">{message}</p>
          {status === "success" && (
            <p className="text-xs text-muted-foreground mt-2">This window will close automatically.</p>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
