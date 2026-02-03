"use client"

import { useState, useEffect } from "react"
import { createClient } from "@/lib/supabase/client"
import { Property, Sentence, LABEL_OPTIONS, LabelType } from "@/lib/types"
import { PropertySelector } from "@/components/property-selector"
import { SentenceLabeler } from "@/components/sentence-labeler"
import { SidebarTrigger } from "@/components/ui/sidebar"
import { Separator } from "@/components/ui/separator"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Button } from "@/components/ui/button"
import { ChevronLeft, ChevronRight, Filter } from "lucide-react"

interface LabelerClientProps {
  properties: Property[]
  userId: string
}

export function LabelerClient({ properties, userId }: LabelerClientProps) {
  const [selectedProperty, setSelectedProperty] = useState<Property | null>(null)
  const [sentences, setSentences] = useState<Sentence[]>([])
  const [currentIndex, setCurrentIndex] = useState(0)
  const [loading, setLoading] = useState(false)
  const [maxLabels, setMaxLabels] = useState<string>("all")
  const supabase = createClient()

  useEffect(() => {
    if (selectedProperty) {
      loadSentences()
    }
  }, [selectedProperty, maxLabels])

  const loadSentences = async () => {
    if (!selectedProperty) return

    setLoading(true)
    let query = supabase
      .from("sentences")
      .select("*")
      .eq("property_id", selectedProperty.id)
      .order("label_count", { ascending: true })

    if (maxLabels !== "all") {
      query = query.lte("label_count", parseInt(maxLabels))
    }

    const { data } = await query
    setSentences(data || [])
    setCurrentIndex(0)
    setLoading(false)
  }

  const handleLabelSubmit = async (
    labelType: LabelType,
    subjectSpan: [number, number] | null,
    objectSpan: [number, number] | null
  ) => {
    if (!selectedProperty || !sentences[currentIndex]) return

    const sentence = sentences[currentIndex]

    const { error } = await supabase.from("labels").insert({
      user_id: userId,
      sentence_id: sentence.id,
      property_id: selectedProperty.id,
      label_type: labelType,
      subject_start: subjectSpan?.[0] ?? null,
      subject_end: subjectSpan?.[1] ?? null,
      object_start: objectSpan?.[0] ?? null,
      object_end: objectSpan?.[1] ?? null,
    })

    if (!error) {
      // Update local sentence label count
      setSentences((prev) =>
        prev.map((s, i) =>
          i === currentIndex ? { ...s, label_count: s.label_count + 1 } : s
        )
      )

      // Move to next sentence
      if (currentIndex < sentences.length - 1) {
        setCurrentIndex(currentIndex + 1)
      }
    }

    return !error
  }

  const currentSentence = sentences[currentIndex]

  return (
    <div className="flex flex-col h-full">
      <header className="flex h-14 shrink-0 items-center gap-2 border-b px-4">
        <SidebarTrigger className="-ml-1" />
        <Separator orientation="vertical" className="mr-2 h-4" />
        <h1 className="text-lg font-semibold">Label Sentences</h1>
        {selectedProperty && (
          <Badge variant="secondary" className="ml-auto">
            {sentences.length} sentences
          </Badge>
        )}
      </header>

      <div className="flex-1 overflow-auto p-4">
        <div className="max-w-4xl mx-auto space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Select Property</CardTitle>
              <CardDescription>
                Choose a property to start labeling its associated sentences
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <PropertySelector
                properties={properties}
                selectedProperty={selectedProperty}
                onSelect={setSelectedProperty}
              />

              {selectedProperty && (
                <div className="grid gap-4 pt-4 border-t">
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-muted-foreground">Domain:</span>{" "}
                      <span className="font-medium">
                        {selectedProperty.domain_label || selectedProperty.domain || "N/A"}
                      </span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Range:</span>{" "}
                      <span className="font-medium">
                        {selectedProperty.range_label || selectedProperty.range || "N/A"}
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center gap-4">
                    <div className="flex items-center gap-2">
                      <Filter className="h-4 w-4 text-muted-foreground" />
                      <Label htmlFor="maxLabels" className="text-sm">
                        Max labels:
                      </Label>
                      <Select value={maxLabels} onValueChange={setMaxLabels}>
                        <SelectTrigger id="maxLabels" className="w-32">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="all">All</SelectItem>
                          <SelectItem value="0">0 labels</SelectItem>
                          <SelectItem value="1">≤ 1 label</SelectItem>
                          <SelectItem value="2">≤ 2 labels</SelectItem>
                          <SelectItem value="3">≤ 3 labels</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {selectedProperty && sentences.length > 0 && currentSentence && (
            <>
              <div className="flex items-center justify-between">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentIndex(Math.max(0, currentIndex - 1))}
                  disabled={currentIndex === 0}
                >
                  <ChevronLeft className="h-4 w-4 mr-1" />
                  Previous
                </Button>
                <span className="text-sm text-muted-foreground">
                  Sentence {currentIndex + 1} of {sentences.length}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() =>
                    setCurrentIndex(Math.min(sentences.length - 1, currentIndex + 1))
                  }
                  disabled={currentIndex === sentences.length - 1}
                >
                  Next
                  <ChevronRight className="h-4 w-4 ml-1" />
                </Button>
              </div>

              <SentenceLabeler
                sentence={currentSentence}
                property={selectedProperty}
                onSubmit={handleLabelSubmit}
              />
            </>
          )}

          {selectedProperty && sentences.length === 0 && !loading && (
            <Card>
              <CardContent className="py-12 text-center">
                <p className="text-muted-foreground">
                  No sentences found for this property with the selected filter.
                </p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}
