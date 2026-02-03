import { createClient } from "@/lib/supabase/server"
import { MyLabelsClient } from "@/components/my-labels-client"

export default async function MyLabelsPage() {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()

  const { data: labels } = await supabase
    .from("labels")
    .select(`
      *,
      sentence:sentences(*),
      property:properties(*)
    `)
    .eq("user_id", user?.id)
    .order("created_at", { ascending: false })

  const { data: properties } = await supabase
    .from("properties")
    .select("*")
    .order("name")

  return (
    <main className="flex-1">
      <MyLabelsClient 
        labels={labels || []} 
        properties={properties || []} 
        userId={user?.id || ""}
      />
    </main>
  )
}
