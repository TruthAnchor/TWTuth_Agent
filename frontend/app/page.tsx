import { SimpleTweetRegistration } from "@/components/simple-tweet-registration"
import { AdvancedTweetRegistration } from "@/components/advanced-tweet-registration"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"

export default function HomePage() {
  return (
    <div className="container mx-auto py-8 px-4 max-w-4xl">
      <div className="mb-8 text-center">
        <h1 className="text-4xl font-bold mb-2">Register Your Tweets as IP</h1>
        <p className="text-muted-foreground">Transform your tweets into intellectual property on the blockchain</p>
      </div>

      <Tabs defaultValue="simple" className="w-full">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="simple">Quick Registration</TabsTrigger>
          <TabsTrigger value="advanced">Advanced Options</TabsTrigger>
        </TabsList>
        <TabsContent value="simple" className="mt-6">
          <SimpleTweetRegistration />
        </TabsContent>
        <TabsContent value="advanced" className="mt-6">
          <AdvancedTweetRegistration />
        </TabsContent>
      </Tabs>
    </div>
  )
}
