"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Compass, ExternalLink, Heart, Repeat2, MessageCircle, Clock, Database } from "lucide-react"
import { useEffect, useState } from "react"
import { ethers } from "ethers"
import { getTweetRegistryContract, type TweetData } from "@/lib/contracts"
import { useToast } from "@/hooks/use-toast"

export default function ExplorePage() {
  const [tweets, setTweets] = useState<TweetData[]>([])
  const [loading, setLoading] = useState(true)
  const [totalCount, setTotalCount] = useState(0)
  const [currentPage, setCurrentPage] = useState(0)
  const { toast } = useToast()
  const TWEETS_PER_PAGE = 10

  useEffect(() => {
    loadTweets()
  }, [currentPage])

  async function loadTweets() {
    try {
      setLoading(true)
      const provider = new ethers.JsonRpcProvider("https://api.node.glif.io/rpc/v1")
      const contract = getTweetRegistryContract(provider)

      const count = await contract.getTotalCount()
      setTotalCount(Number(count))

      if (Number(count) === 0) {
        setTweets([])
        setLoading(false)
        return
      }

      const offset = currentPage * TWEETS_PER_PAGE
      const limit = Math.min(TWEETS_PER_PAGE, Number(count) - offset)
      const hashes = await contract.getAllTweetHashes(offset, limit)

      const tweetDataPromises = hashes.map(async (hash: string) => {
        try {
          const data = await contract.getTweet(hash)
          return data
        } catch (error) {
          console.error("Error fetching tweet:", error)
          return null
        }
      })

      const tweetData = await Promise.all(tweetDataPromises)
      setTweets(tweetData.filter((t): t is TweetData => t !== null))
    } catch (error) {
      console.error("Error loading tweets:", error)
      toast({
        title: "Error loading tweets",
        description: "Failed to fetch tweets from the blockchain. Please try again.",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  const totalPages = Math.ceil(totalCount / TWEETS_PER_PAGE)

  if (loading) {
    return (
      <div className="container mx-auto py-8 px-4 max-w-6xl">
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-2">Explore Anchored Tweets</h1>
          <p className="text-muted-foreground">
            Discover tweets that have been permanently timestamped on the Filecoin blockchain
          </p>
        </div>
        <Card>
          <CardContent className="py-12">
            <div className="flex items-center justify-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
              <span className="ml-3 text-muted-foreground">Loading anchored tweets...</span>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (tweets.length === 0) {
    return (
      <div className="container mx-auto py-8 px-4 max-w-6xl">
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-2">Explore Anchored Tweets</h1>
          <p className="text-muted-foreground">
            Discover tweets that have been permanently timestamped on the Filecoin blockchain
          </p>
        </div>
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Compass className="w-5 h-5" />
              No Tweets Yet
            </CardTitle>
            <CardDescription>Be the first to anchor a tweet on the blockchain!</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              No tweets have been anchored yet. Head to the home page to anchor your first tweet.
            </p>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="container mx-auto py-8 px-4 max-w-6xl">
      <div className="mb-8">
        <h1 className="text-4xl font-bold mb-2">Explore Anchored Tweets</h1>
        <p className="text-muted-foreground">
          Discover tweets that have been permanently timestamped on the Filecoin blockchain
        {/* --- FIX: Was </Top> --- */}
        </p>
        {totalCount > 0 && (
          <p className="text-sm text-muted-foreground mt-2">
            {totalCount} tweet{totalCount !== 1 ? "s" : ""} anchored
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

        {totalPages > 1 && (
          <div className="flex items-center justify-center gap-2 pt-4">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCurrentPage((p) => Math.max(0, p - 1))}
              disabled={currentPage === 0}
            >
              Previous
            </Button>
            <span className="text-sm text-muted-foreground">
              Page {currentPage + 1} of {totalPages}
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCurrentPage((p) => Math.min(totalPages - 1, p + 1))}
              disabled={currentPage >= totalPages - 1}
            >
              Next
            </Button>
          </div>
        )}
      </div>
    </div>
  )
}