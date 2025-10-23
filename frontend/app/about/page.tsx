import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Info, Shield, Zap, Globe } from "lucide-react"

export default function AboutPage() {
  return (
    <div className="container mx-auto py-8 px-4 max-w-4xl">
      <div className="mb-8 text-center">
        <h1 className="text-4xl font-bold mb-2">About TruthAnchor</h1>
        <p className="text-muted-foreground">Protecting market moving tweets through blockchain technology</p>
      </div>

      <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Info className="w-5 h-5" />
              What is TruthAnchor?
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              TruthAnchor is a revolutionary platform that allows content to be storred immutably on the blockchain. By leveraging Filecoin, we provide immutable
              proof of ownership.
            </p>
          </CardContent>
        </Card>

        <div className="grid md:grid-cols-3 gap-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg">
                <Shield className="w-4 h-4" />
                Protect
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                Secure your creative work with blockchain-verified ownership
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg">
                <Zap className="w-4 h-4" />
                Monetize
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">Earn revenue through licensing and derivative works</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg">
                <Globe className="w-4 h-4" />
                Decentralized
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">Built on open protocols for transparency and permanence</p>
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>How It Works</CardTitle>
          </CardHeader>
          <CardContent>
            <ol className="list-decimal list-inside space-y-2 text-sm text-muted-foreground">
              <li>Connect your Web3 wallet and Twitter account</li>
              <li>Paste the URL of the tweet you want to register</li>
              <li>Configure licensing terms and collection settings</li>
              <li>Submit the transaction to register your IP on-chain</li>
              <li>Receive an NFT representing ownership of your tweet IP</li>
            </ol>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
