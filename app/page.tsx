import { createClient } from "@/lib/supabase/server"
import { redirect } from "next/navigation"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Tag, ArrowRight } from "lucide-react"

export default async function HomePage() {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()

  if (user) {
    redirect("/labeler")
  }

  return (
    <main className="min-h-screen flex flex-col">
      <header className="border-b">
        <div className="container mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-md bg-primary">
              <Tag className="h-4 w-4 text-primary-foreground" />
            </div>
            <span className="font-semibold">Property Labeler</span>
          </div>
          <div className="flex items-center gap-4">
            <Link href="/auth/login">
              <Button variant="ghost">Sign In</Button>
            </Link>
            <Link href="/auth/sign-up">
              <Button>Get Started</Button>
            </Link>
          </div>
        </div>
      </header>

      <section className="flex-1 flex items-center justify-center">
        <div className="container mx-auto px-4 py-24 text-center">
          <div className="max-w-3xl mx-auto space-y-8">
            <div className="inline-flex items-center gap-2 rounded-full border px-4 py-1.5 text-sm">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-primary"></span>
              </span>
              Ontology Corpus Labeling Tool
            </div>

            <h1 className="text-4xl sm:text-5xl md:text-6xl font-bold tracking-tight text-balance">
              Property Sentence Labeler
            </h1>

            <p className="text-xl text-muted-foreground max-w-2xl mx-auto text-pretty">
              A collaborative tool for labeling sentences with ontology properties. 
              Identify domain-range alignments, select subject and object spans, 
              and build high-quality training datasets.
            </p>

            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link href="/auth/sign-up">
                <Button size="lg" className="gap-2">
                  Start Labeling
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </Link>
              <Link href="/auth/login">
                <Button size="lg" variant="outline">
                  Sign In
                </Button>
              </Link>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 pt-12">
              <div className="rounded-lg border bg-card p-6 text-left">
                <h3 className="font-semibold mb-2">Label Types</h3>
                <p className="text-sm text-muted-foreground">
                  Five distinct label categories for precise alignment classification
                </p>
              </div>
              <div className="rounded-lg border bg-card p-6 text-left">
                <h3 className="font-semibold mb-2">Word Selection</h3>
                <p className="text-sm text-muted-foreground">
                  Interactive subject and object span selection for detailed annotations
                </p>
              </div>
              <div className="rounded-lg border bg-card p-6 text-left">
                <h3 className="font-semibold mb-2">Export Data</h3>
                <p className="text-sm text-muted-foreground">
                  Download labeled data in JSON format for model training
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <footer className="border-t py-8">
        <div className="container mx-auto px-4 text-center text-sm text-muted-foreground">
          Property Sentence Labeler - Ontology Corpus Annotation Tool
        </div>
      </footer>
    </main>
  )
}
