import { createClient } from "@/lib/supabase/server"
import { ExportClient } from "@/components/export-client"

export default async function ExportPage() {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()

  const { data: properties } = await supabase
    .from("properties")
    .select("*")
    .order("name")

  return (
    <main className="flex-1">
      <ExportClient properties={properties || []} userId={user?.id || ""} />
    </main>
  )
}
