import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Users, Twitter, MessageCircle, Github } from "lucide-react"
import { Button } from "@/components/ui/button"

export default function CommunityPage() {
  return (
    <div className="container mx-auto py-8 px-4 max-w-4xl">
      <div className="mb-8 text-center">
        <h1 className="text-4xl font-bold mb-2">Join Our Community</h1>
        <p className="text-muted-foreground">Connect with creators, developers, and IP enthusiasts</p>
      </div>

      <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="w-5 h-5" />
              Community Channels
            </CardTitle>
            <CardDescription>Stay connected and get support from our community</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid md:grid-cols-2 gap-4">
              <Button variant="outline" className="justify-start gap-2 h-auto py-4 bg-transparent">
                <Twitter className="w-5 h-5" />
                <div className="text-left">
                  <div className="font-medium">Twitter</div>
                  <div className="text-xs text-muted-foreground">Follow for updates</div>
                </div>
              </Button>

              <Button variant="outline" className="justify-start gap-2 h-auto py-4 bg-transparent">
                <MessageCircle className="w-5 h-5" />
                <div className="text-left">
                  <div className="font-medium">Discord</div>
                  <div className="text-xs text-muted-foreground">Join the conversation</div>
                </div>
              </Button>

              <Button variant="outline" className="justify-start gap-2 h-auto py-4 bg-transparent">
                <Github className="w-5 h-5" />
                <div className="text-left">
                  <div className="font-medium">GitHub</div>
                  <div className="text-xs text-muted-foreground">Contribute to the project</div>
                </div>
              </Button>

              <Button variant="outline" className="justify-start gap-2 h-auto py-4 bg-transparent">
                <Users className="w-5 h-5" />
                <div className="text-left">
                  <div className="font-medium">Forum</div>
                  <div className="text-xs text-muted-foreground">Discuss and share ideas</div>
                </div>
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Get Involved</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground mb-4">
              TruthAnchor for the community. We welcome contributions from developers, designers, and
              content creators who share our vision of protecting digital content.
            </p>
            <ul className="list-disc list-inside space-y-2 text-sm text-muted-foreground">
              <li>Report bugs and suggest features on GitHub</li>
              <li>Share your success stories with the community</li>
              <li>Help other creators get started</li>
              <li>Contribute to documentation and tutorials</li>
            </ul>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
