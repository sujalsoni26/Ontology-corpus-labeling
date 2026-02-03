"use client"

import { useState } from "react"
import { createClient } from "@/lib/supabase/client"
import { Property, LABEL_OPTIONS } from "@/lib/types"
import { SidebarTrigger } from "@/components/ui/sidebar"
import { Separator } from "@/components/ui/separator"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Checkbox } from "@/components/ui/checkbox"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Download, Loader2, FileJson } from "lucide-react"

interface ExportClientProps {
  properties: Property[]
  userId: string
}

export function ExportClient({ properties, userId }: ExportClientProps) {
  const [selectedProperty, setSelectedProperty] = useState<string>("all")
  const [myLabelsOnly, setMyLabelsOnly] = useState(false)
  const [loading, setLoading] = useState(false)
  const supabase = createClient()

  const handleExport = async () => {
    setLoading(true)

    let query = supabase
      .from("labels")
      .select(`
        *,
        sentence:sentences(*),
        property:properties(*)
      `)

    if (myLabelsOnly) {
      query = query.eq("user_id", userId)
    }

    if (selectedProperty !== "all") {
      query = query.eq("property_id", selectedProperty)
    }

    const { data: labels } = await query

    if (labels) {
      const exportData = labels.map((label) => ({
        label_id: label.id,
        sentence_id: label.sentence_id,
        sentence_text: label.sentence?.text,
        property_id: label.property_id,
        property_name: label.property?.name,
        property_iri: label.property?.iri,
        domain: label.property?.domain,
        domain_label: label.property?.domain_label,
        range: label.property?.range,
        range_label: label.property?.range_label,
        label_type: label.label_type,
        label_description: LABEL_OPTIONS.find((o) => o.value === label.label_type)?.description,
        subject_start: label.subject_start,
        subject_end: label.subject_end,
        subject_text: label.subject_start !== null && label.subject_end !== null
          ? label.sentence?.text.split(/\s+/).slice(label.subject_start, label.subject_end + 1).join(" ")
          : null,
        object_start: label.object_start,
        object_end: label.object_end,
        object_text: label.object_start !== null && label.object_end !== null
          ? label.sentence?.text.split(/\s+/).slice(label.object_start, label.object_end + 1).join(" ")
          : null,
        created_at: label.created_at,
      }))

      const blob = new Blob([JSON.stringify(exportData, null, 2)], {
        type: "application/json",
      })
      const url = URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      a.download = `labels-export-${new Date().toISOString().split("T")[0]}.json`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    }

    setLoading(false)
  }

  return (
    <div className="flex flex-col h-full">
      <header className="flex h-14 shrink-0 items-center gap-2 border-b px-4">
        <SidebarTrigger className="-ml-1" />
        <Separator orientation="vertical" className="mr-2 h-4" />
        <h1 className="text-lg font-semibold">Export Data</h1>
      </header>

      <div className="flex-1 overflow-auto p-4">
        <div className="max-w-2xl mx-auto space-y-6">
          <Card>
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                  <FileJson className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <CardTitle>Export Labels</CardTitle>
                  <CardDescription>
                    Download your labeled data in JSON format
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="property">Filter by Property</Label>
                <Select value={selectedProperty} onValueChange={setSelectedProperty}>
                  <SelectTrigger id="property">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Properties</SelectItem>
                    {properties.map((property) => (
                      <SelectItem key={property.id} value={property.id}>
                        {property.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="flex items-center space-x-2">
                <Checkbox
                  id="myLabels"
                  checked={myLabelsOnly}
                  onCheckedChange={(checked) => setMyLabelsOnly(checked === true)}
                />
                <Label
                  htmlFor="myLabels"
                  className="text-sm font-medium leading-none cursor-pointer"
                >
                  Export only my labels
                </Label>
              </div>

              <div className="rounded-lg bg-muted p-4">
                <h4 className="font-medium mb-2">Export includes:</h4>
                <ul className="text-sm text-muted-foreground space-y-1">
                  <li>- Sentence text and ID</li>
                  <li>- Property name, IRI, domain, and range</li>
                  <li>- Label type and description</li>
                  <li>- Subject and object word selections</li>
                  <li>- Timestamp</li>
                </ul>
              </div>

              <Button onClick={handleExport} disabled={loading} className="w-full">
                {loading ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin mr-2" />
                    Preparing Export...
                  </>
                ) : (
                  <>
                    <Download className="h-4 w-4 mr-2" />
                    Download JSON
                  </>
                )}
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
