import { type NextRequest, NextResponse } from "next/server"

// Twitter OAuth configuration
const TWITTER_CLIENT_ID = process.env.NEXT_PUBLIC_TWITTER_CLIENT_ID || process.env.TWITTER_CLIENT_ID
const TWITTER_CLIENT_SECRET = process.env.TWITTER_CLIENT_SECRET
const BASE_URL =
  process.env.NEXT_PUBLIC_BASE_URL ||
  (process.env.NODE_ENV === "production" ? "https://tweet-ip.vercel.app" : "http://localhost:3000")
const REDIRECT_URI = `${BASE_URL}/twitter-callback`

export async function POST(request: NextRequest) {
  try {
    const { code, codeVerifier, redirectUri } = await request.json()

    console.log("Twitter exchange - Received request with:", {
      hasCode: !!code,
      hasCodeVerifier: !!codeVerifier,
      providedRedirectUri: redirectUri,
    })

    if (!code || !codeVerifier) {
      return NextResponse.json({ error: "Missing code or code verifier" }, { status: 400 })
    }

    if (!TWITTER_CLIENT_ID || !TWITTER_CLIENT_SECRET) {
      console.error("Twitter credentials not configured:", {
        hasClientId: !!TWITTER_CLIENT_ID,
        hasClientSecret: !!TWITTER_CLIENT_SECRET,
      })
      return NextResponse.json({ error: "Twitter credentials not configured" }, { status: 500 })
    }

    // Use the redirect URI that was used during the authorization request
    // This is critical - it must match exactly what was used when getting the code
    const finalRedirectUri = redirectUri || REDIRECT_URI

    console.log("Twitter exchange - Using configuration:", {
      clientIdLength: TWITTER_CLIENT_ID.length,
      clientSecretLength: TWITTER_CLIENT_SECRET.length,
      redirectUri: finalRedirectUri,
      baseUrl: BASE_URL,
    })

    // Step 1: Exchange the authorization code for an access token
    const tokenParams = new URLSearchParams({
      code,
      grant_type: "authorization_code",
      client_id: TWITTER_CLIENT_ID,
      redirect_uri: finalRedirectUri,
      code_verifier: codeVerifier,
    })

    console.log("Twitter exchange - Token request params:", tokenParams.toString())

    const tokenResponse = await fetch("https://api.twitter.com/2/oauth2/token", {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
        Authorization: `Basic ${Buffer.from(`${TWITTER_CLIENT_ID}:${TWITTER_CLIENT_SECRET}`).toString("base64")}`,
      },
      body: tokenParams.toString(),
    })

    const tokenResponseStatus = tokenResponse.status
    const tokenResponseText = await tokenResponse.text()

    console.log("Twitter exchange - Token response:", {
      status: tokenResponseStatus,
      body: tokenResponseText,
    })

    if (!tokenResponse.ok) {
      return NextResponse.json(
        {
          error: "Failed to exchange code for token",
          details: tokenResponseText,
          status: tokenResponseStatus,
        },
        { status: 400 },
      )
    }

    const tokenData = JSON.parse(tokenResponseText)
    const { access_token } = tokenData

    // Step 2: Use the access token to fetch the user's profile
    console.log("Twitter exchange - Fetching user data with access token")

    const userResponse = await fetch("https://api.twitter.com/2/users/me", {
      headers: {
        Authorization: `Bearer ${access_token}`,
      },
    })

    const userResponseStatus = userResponse.status
    const userResponseText = await userResponse.text()

    console.log("Twitter exchange - User response:", {
      status: userResponseStatus,
      body: userResponseText,
    })

    if (!userResponse.ok) {
      return NextResponse.json(
        {
          error: "Failed to fetch user data",
          details: userResponseText,
          status: userResponseStatus,
        },
        { status: 400 },
      )
    }

    const userData = JSON.parse(userResponseText)

    // Return the user data
    return NextResponse.json({
      username: userData.data.username,
      id: userData.data.id,
      name: userData.data.name,
    })
  } catch (error) {
    console.error("Error in Twitter token exchange:", error)
    return NextResponse.json(
      {
        error: "Internal server error",
        details: error instanceof Error ? error.message : String(error),
      },
      { status: 500 },
    )
  }
}
