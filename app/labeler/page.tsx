import { createClient } from "@/lib/supabase/server"
import { LabelerClient } from "@/components/labeler-client"

export default async function LabelerPage() {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()

  const { data: properties } = await supabase
    .from("properties")
    .select("*")
    .order("name")

  return (
    <main className="flex-1">
      <LabelerClient 
        properties={properties || []} 
        userId={user?.id || ""} 
      />
    </main>
  )
}
