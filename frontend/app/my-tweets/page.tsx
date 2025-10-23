"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { MessageSquare, ExternalLink, Heart, Repeat2, MessageCircle, Clock, Database, Wallet } from "lucide-react" // Added Wallet icon
import { useEffect, useState } from "react"
import { ethers } from "ethers"
import { getTweetRegistryContract, type TweetData } from "@/lib/contracts"
import { useToast } from "@/hooks/use-toast"
// --- MODIFICATION START ---
// We no longer need the Twitter hook on this page
// import { useTwitterConnection } from "@/hooks/use-twitter-connection" 
import { useTomoWallet } from "@/contexts/tomo-wallet-context"
import { useFallbackWallet } from "@/contexts/fallback-wallet-context"
// --- MODIFICATION END ---

export default function MyTweetsPage() {
  const [tweets, setTweets] = useState<TweetData[]>([])
  const [loading, setLoading] = useState(false)
  const [totalCount, setTotalCount] = useState(0)
  const { toast } = useToast()

  // --- MODIFICATION START ---
  // Removed all twitter-related state
  // const { handle, isConnected: twitterConnected } = useTwitterConnection()

  // Use the same wallet logic as the sidebar
  const tomoWallet = useTomoWallet()
  const fallbackWallet = useFallbackWallet()
  const wallet = tomoWallet.isConnected ? tomoWallet : fallbackWallet
  // Destructure for convenience
  const { address, isConnected: walletConnected } = wallet
  // --- MODIFICATION END ---

  useEffect(() => {
    // --- MODIFICATION START ---
    // Update dependencies to only check for wallet connection and address
    if (walletConnected && address) {
      loadMyTweets()
    }
    // --- MODIFICATION END ---
  }, [walletConnected, address])

  async function loadMyTweets() {
    if (!address) return // Guard clause

    try {
      setLoading(true)
      const provider = new ethers.JsonRpcProvider("https://api.node.glif.io/rpc/v1")
      const contract = getTweetRegistryContract(provider)

      // 1. Get total count of ALL tweets
      const count = await contract.getTotalCount()
      if (Number(count) === 0) {
        setTweets([])
        setLoading(false);
        return
      }

      // 2. Get hashes for ALL tweets
      const hashes = await contract.getAllTweetHashes(0, Number(count))

      // 3. Fetch data for all tweets
      const tweetDataPromises = hashes.map(async (hash: string) => {
        try {
          const data = await contract.getTweet(hash)
          return data
        } catch (error) {
          console.error("Error fetching tweet:", error)
          return null
        }
      })

      const allTweets = await Promise.all(tweetDataPromises)
      const allValidTweets = allTweets.filter((t): t is TweetData => t !== null)

      // 4. Filter on the client-side by submitter address
      const lowerCaseAddress = address.toLowerCase()
      const myTweets = allValidTweets.filter(
        (tweet) => tweet.meta.submitter.toLowerCase() === lowerCaseAddress
      )

      setTweets(myTweets)
      setTotalCount(myTweets.length)
    } catch (error) {
      console.error("Error loading my tweets:", error)
      toast({
        title: "Error loading your tweets",
        description: "Failed to fetch all tweets from the blockchain. Please try again.",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  // --- MODIFICATION START ---
  // This guard now ONLY checks for wallet connection
  if (!walletConnected) {
    return (
      <div className="container mx-auto py-8 px-4 max-w-6xl">
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-2">My Anchored Tweets</h1>
          <p className="text-muted-foreground">View and manage your tweets anchored on the blockchain</p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Wallet className="w-5 h-5" /> {/* Changed icon */}
              Connect Wallet to View Your Tweets
            </CardTitle>
            <CardDescription>
              Connect your wallet to view your anchored tweets.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Please connect your wallet using the sidebar to view your anchored tweet portfolio.
            </p>
          </CardContent>
        </Card>
      </div>
    )
  }
  // --- MODIFICATION END ---

  // Loading state
  if (loading) {
    return (
      <div className="container mx-auto py-8 px-4 max-w-6xl">
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-2">My Anchored Tweets</h1>
          <p className="text-muted-foreground">View and manage your tweets anchored on the blockchain</p>
        </div>
        <Card>
          <CardContent className="py-12">
            <div className="flex items-center justify-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
              <span className="ml-3 text-muted-foreground">Loading your anchored tweets...</span>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  // "No Tweets" message
  if (tweets.length === 0) {
    return (
      <div className="container mx-auto py-8 px-4 max-w-6xl">
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-2">My Anchored Tweets</h1>
          <p className="text-muted-foreground">View and manage your tweets anchored on the blockchain</p>
        </div>
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <MessageSquare className="w-5 h-5" />
              No Tweets Found
            </CardTitle>
            <CardDescription>
              We could not find any tweets anchored by your connected wallet address.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Head to the home page to anchor your first tweet. If you just submitted one, it may take a few moments
              to appear.
            </p>
          </CardContent>
        </Card>
      </div>
    )
  }

  // Render the list of tweets
  return (
    <div className="container mx-auto py-8 px-4 max-w-6xl">
      <div className="mb-8">
        <h1 className="text-4xl font-bold mb-2">My Anchored Tweets</h1>
        <p className="text-muted-foreground">View and manage your tweets anchored on the blockchain</p>
        {totalCount > 0 && (
          <p className="text-sm text-muted-foreground mt-2">
            You have {totalCount} tweet{totalCount !== 1 ? "s" : ""} anchored
          </p>
        )}
      </div>

      <div className="space-y-4">
        {tweets.map((tweet) => {
          const tweetHash = tweet.identity.tweetHash
          const handle = tweet.identity.handle
          const verified = tweet.identity.verified
          const user = tweet.identity.user
          const tweetURL = tweet.identity.tweetURL
          const content = tweet.content
          const likes = Number(tweet.metrics.likes)
          const retweets = Number(tweet.metrics.retweets)
          const replies = Number(tweet.metrics.replies)
          const timestamp = Number(tweet.metrics.timestamp)
          const ecosystem = tweet.storageData.ecosystem
          const ipfsScreenshotCID = tweet.storageData.ipfsScreenshotCID
          const filecoinRootCID = tweet.storageData.filecoinRootCID
          const processedAt = Number(tweet.meta.processedAt)

          return (
            <Card key={tweetHash} className="hover:shadow-lg transition-shadow">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <CardTitle className="text-lg flex items-center gap-2">
                      <span>@{handle}</span>
                      {verified && (
                        <Badge variant="secondary" className="text-xs">
                          Verified
                        </Badge>
                      )}
                    </CardTitle>
                    <CardDescription className="mt-1">{user}</CardDescription>
                  </div>
                  <Button variant="ghost" size="sm" asChild>
                    <a href={tweetURL} target="_blank" rel="noopener noreferrer">
                      <ExternalLink className="w-4 h-4" />
                    </a>
                  </Button>
                </div>
              </CardHeader>

              <CardContent>
                <div className="flex flex-col md:flex-row md:gap-6">
                  {/* Left Column: Tweet Info */}
                  <div className="flex-1 space-y-4">
                    <p className="text-sm whitespace-pre-wrap">{content}</p>

                    <div className="flex flex-wrap items-center gap-4 text-sm text-muted-foreground">
                      <span className="flex items-center gap-1">
                        <Heart className="w-4 h-4" />
                        {likes.toLocaleString()}
                      </span>
                      <span className="flex items-center gap-1">
                        <Repeat2 className="w-4 h-4" />
                        {retweets.toLocaleString()}
                      </span>
                      <span className="flex items-center gap-1">
                        <MessageCircle className="w-4 h-4" />
                        {replies.toLocaleString()}
                      </span>
                      <span className="flex items-center gap-1">
                        <Clock className="w-4 h-4" />
                        {new Date(timestamp * 1000).toLocaleDateString()}
                      </span>
                    </div>

                    <div className="pt-4 border-t space-y-2">
                      <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        <Database className="w-3 h-3" />
                        <span>Stored on Filecoin</span>
                        {ecosystem && (
                          <Badge variant="outline" className="text-xs">
                            {ecosystem}
                          </Badge>
                        )}
                      </div>
                      {filecoinRootCID && (
                        <div className="text-xs">
                          <span className="text-muted-foreground">Filecoin CID: </span>
                          <span className="font-mono break-all">{filecoinRootCID}</span>
                        </div>
                      )}
                      <div className="text-xs text-muted-foreground">
                        Anchored {new Date(processedAt * 1000).toLocaleString()}
                      </div>
                    </div>
                  </div>

                  {/* Right Column: Screenshot */}
                  {ipfsScreenshotCID && (
                    <div className="md:w-1/3 mt-4 md:mt-0">
                      <a
                        href={`https://ipfs.io/ipfs/${ipfsScreenshotCID}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="block"
                      >
                        <span className="text-xs font-medium text-muted-foreground">Screenshot</span>
                        <img
                          src={`https://ipfs.io/ipfs/${ipfsScreenshotCID}`}
                          alt={`Screenshot of tweet ${tweetHash}`}
                          className="mt-1 rounded-md border w-full h-auto hover:opacity-90 transition-opacity"
                          loading="lazy"
                        />
                      </a>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>
    </div>
  )
}