import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Map, CheckCircle, Circle } from "lucide-react"

export default function RoadmapPage() {
  const roadmapItems = [
    {
      phase: "Phase 1",
      title: "Core Platform",
      status: "completed",
      items: [
        "Twitter OAuth integration",
        "Wallet connection (Tomo + Fallback)",
        "Simple tweet registration",
        "Advanced configuration options",
      ],
    },
    {
      phase: "Phase 2",
      title: "Discovery & Management",
      status: "in-progress",
      items: [
        "Explore registered IPs",
        "User portfolio dashboard",
        "Search and filter functionality",
        "IP analytics and insights",
      ],
    },
    {
      phase: "Phase 3",
      title: "Licensing & Monetization",
      status: "planned",
      items: ["License marketplace", "Derivative work tracking", "Revenue distribution", "Royalty management"],
    },
    {
      phase: "Phase 4",
      title: "Community & Growth",
      status: "planned",
      items: ["Creator verification badges", "Community governance", "Multi-platform support", "Mobile app"],
    },
  ]

  return (
    <div className="container mx-auto py-8 px-4 max-w-4xl">
      <div className="mb-8 text-center">
        <h1 className="text-4xl font-bold mb-2">Product Roadmap</h1>
        <p className="text-muted-foreground">Our vision for the future of digital content ownership</p>
      </div>

      <div className="space-y-6">
        {roadmapItems.map((item, index) => (
          <Card key={index}>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                  <Map className="w-5 h-5" />
                  {item.phase}: {item.title}
                </CardTitle>
                <span
                  className={`text-xs px-2 py-1 rounded-full ${
                    item.status === "completed"
                      ? "bg-green-500/10 text-green-500"
                      : item.status === "in-progress"
                        ? "bg-blue-500/10 text-blue-500"
                        : "bg-muted text-muted-foreground"
                  }`}
                >
                  {item.status === "completed"
                    ? "Completed"
                    : item.status === "in-progress"
                      ? "In Progress"
                      : "Planned"}
                </span>
              </div>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2">
                {item.items.map((feature, idx) => (
                  <li key={idx} className="flex items-center gap-2 text-sm">
                    {item.status === "completed" ? (
                      <CheckCircle className="w-4 h-4 text-green-500" />
                    ) : (
                      <Circle className="w-4 h-4 text-muted-foreground" />
                    )}
                    <span className={item.status === "completed" ? "text-foreground" : "text-muted-foreground"}>
                      {feature}
                    </span>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
