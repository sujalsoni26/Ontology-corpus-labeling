"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { createClient } from "@/lib/supabase/client"
import { Property, LabelWithDetails, LABEL_OPTIONS, LabelType } from "@/lib/types"
import { SidebarTrigger } from "@/components/ui/sidebar"
import { Separator } from "@/components/ui/separator"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { WordSelector } from "@/components/word-selector"
import { Search, Edit, Trash2, Filter } from "lucide-react"

interface MyLabelsClientProps {
  labels: LabelWithDetails[]
  properties: Property[]
  userId: string
}

export function MyLabelsClient({ labels: initialLabels, properties, userId }: MyLabelsClientProps) {
  const [labels, setLabels] = useState(initialLabels)
  const [searchQuery, setSearchQuery] = useState("")
  const [propertyFilter, setPropertyFilter] = useState<string>("all")
  const [labelTypeFilter, setLabelTypeFilter] = useState<string>("all")
  const [editingLabel, setEditingLabel] = useState<LabelWithDetails | null>(null)
  const [deletingLabel, setDeletingLabel] = useState<LabelWithDetails | null>(null)
  const [editLabelType, setEditLabelType] = useState<LabelType | null>(null)
  const [editSubjectSpan, setEditSubjectSpan] = useState<[number, number] | null>(null)
  const [editObjectSpan, setEditObjectSpan] = useState<[number, number] | null>(null)
  const router = useRouter()
  const supabase = createClient()

  const filteredLabels = labels.filter((label) => {
    const matchesSearch = label.sentence?.text
      .toLowerCase()
      .includes(searchQuery.toLowerCase())
    const matchesProperty =
      propertyFilter === "all" || label.property_id === propertyFilter
    const matchesLabelType =
      labelTypeFilter === "all" || label.label_type === labelTypeFilter
    return matchesSearch && matchesProperty && matchesLabelType
  })

  const handleEdit = (label: LabelWithDetails) => {
    setEditingLabel(label)
    setEditLabelType(label.label_type)
    setEditSubjectSpan(
      label.subject_start !== null && label.subject_end !== null
        ? [label.subject_start, label.subject_end]
        : null
    )
    setEditObjectSpan(
      label.object_start !== null && label.object_end !== null
        ? [label.object_start, label.object_end]
        : null
    )
  }

  const handleSaveEdit = async () => {
    if (!editingLabel || !editLabelType) return

    const { error } = await supabase
      .from("labels")
      .update({
        label_type: editLabelType,
        subject_start: editSubjectSpan?.[0] ?? null,
        subject_end: editSubjectSpan?.[1] ?? null,
        object_start: editObjectSpan?.[0] ?? null,
        object_end: editObjectSpan?.[1] ?? null,
      })
      .eq("id", editingLabel.id)

    if (!error) {
      setLabels((prev) =>
        prev.map((l) =>
          l.id === editingLabel.id
            ? {
                ...l,
                label_type: editLabelType,
                subject_start: editSubjectSpan?.[0] ?? null,
                subject_end: editSubjectSpan?.[1] ?? null,
                object_start: editObjectSpan?.[0] ?? null,
                object_end: editObjectSpan?.[1] ?? null,
              }
            : l
        )
      )
      setEditingLabel(null)
    }
  }

  const handleDelete = async () => {
    if (!deletingLabel) return

    const { error } = await supabase
      .from("labels")
      .delete()
      .eq("id", deletingLabel.id)

    if (!error) {
      setLabels((prev) => prev.filter((l) => l.id !== deletingLabel.id))
      setDeletingLabel(null)
    }
  }

  const getLabelOption = (type: string) =>
    LABEL_OPTIONS.find((o) => o.value === type)

  const needsSubject = editLabelType === "pdr" || editLabelType === "pd"
  const needsObject = editLabelType === "pdr" || editLabelType === "pr"

  return (
    <div className="flex flex-col h-full">
      <header className="flex h-14 shrink-0 items-center gap-2 border-b px-4">
        <SidebarTrigger className="-ml-1" />
        <Separator orientation="vertical" className="mr-2 h-4" />
        <h1 className="text-lg font-semibold">My Labels</h1>
        <Badge variant="secondary" className="ml-auto">
          {labels.length} total
        </Badge>
      </header>

      <div className="flex-1 overflow-auto p-4">
        <div className="max-w-4xl mx-auto space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Filter className="h-5 w-5" />
                Filter Labels
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 md:grid-cols-3">
                <div className="space-y-2">
                  <Label htmlFor="search">Search</Label>
                  <div className="relative">
                    <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                    <Input
                      id="search"
                      placeholder="Search sentences..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="pl-8"
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="property">Property</Label>
                  <Select value={propertyFilter} onValueChange={setPropertyFilter}>
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
                <div className="space-y-2">
                  <Label htmlFor="labelType">Label Type</Label>
                  <Select value={labelTypeFilter} onValueChange={setLabelTypeFilter}>
                    <SelectTrigger id="labelType">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Types</SelectItem>
                      {LABEL_OPTIONS.map((option) => (
                        <SelectItem key={option.value} value={option.value}>
                          {option.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </CardContent>
          </Card>

          <div className="space-y-4">
            {filteredLabels.length === 0 ? (
              <Card>
                <CardContent className="py-12 text-center">
                  <p className="text-muted-foreground">
                    {labels.length === 0
                      ? "You haven't labeled any sentences yet."
                      : "No labels match your filters."}
                  </p>
                </CardContent>
              </Card>
            ) : (
              filteredLabels.map((label) => {
                const labelOption = getLabelOption(label.label_type)
                const words = label.sentence?.text.split(/\s+/) || []

                return (
                  <Card key={label.id}>
                    <CardHeader className="pb-2">
                      <div className="flex items-start justify-between">
                        <div>
                          <CardTitle className="text-base">
                            {label.property?.name}
                          </CardTitle>
                          <CardDescription>
                            {new Date(label.created_at).toLocaleDateString()}
                          </CardDescription>
                        </div>
                        <div className="flex items-center gap-2">
                          <Badge
                            className={`${labelOption?.color} text-primary-foreground`}
                          >
                            {labelOption?.label}
                          </Badge>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => handleEdit(label)}
                          >
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => setDeletingLabel(label)}
                          >
                            <Trash2 className="h-4 w-4 text-destructive" />
                          </Button>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <p className="rounded-lg bg-muted p-3 text-sm">
                        {label.sentence?.text}
                      </p>
                      {(label.subject_start !== null || label.object_start !== null) && (
                        <div className="mt-2 flex gap-4 text-xs">
                          {label.subject_start !== null && label.subject_end !== null && (
                            <span>
                              <strong>Subject:</strong>{" "}
                              {words.slice(label.subject_start, label.subject_end + 1).join(" ")}
                            </span>
                          )}
                          {label.object_start !== null && label.object_end !== null && (
                            <span>
                              <strong>Object:</strong>{" "}
                              {words.slice(label.object_start, label.object_end + 1).join(" ")}
                            </span>
                          )}
                        </div>
                      )}
                    </CardContent>
                  </Card>
                )
              })
            )}
          </div>
        </div>
      </div>

      {/* Edit Dialog */}
      <Dialog open={!!editingLabel} onOpenChange={() => setEditingLabel(null)}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Edit Label</DialogTitle>
            <DialogDescription>
              Update the label for this sentence.
            </DialogDescription>
          </DialogHeader>
          {editingLabel && (
            <div className="space-y-4">
              <div className="rounded-lg bg-muted p-3">
                <p>{editingLabel.sentence?.text}</p>
              </div>

              <RadioGroup
                value={editLabelType || ""}
                onValueChange={(value) => {
                  setEditLabelType(value as LabelType)
                  if (value === "p" || value === "n") {
                    setEditSubjectSpan(null)
                    setEditObjectSpan(null)
                  }
                }}
                className="grid gap-2"
              >
                {LABEL_OPTIONS.map((option) => (
                  <div key={option.value} className="flex items-center space-x-3">
                    <RadioGroupItem value={option.value} id={`edit-${option.value}`} />
                    <Label
                      htmlFor={`edit-${option.value}`}
                      className="flex-1 cursor-pointer flex items-center gap-2"
                    >
                      <div className={`w-3 h-3 rounded-full ${option.color}`} />
                      <span className="font-medium">{option.label}</span>
                    </Label>
                  </div>
                ))}
              </RadioGroup>

              {needsSubject && (
                <div className="space-y-2">
                  <Label className="text-sm font-medium">Subject Words</Label>
                  <WordSelector
                    words={editingLabel.sentence?.text.split(/\s+/) || []}
                    selection={editSubjectSpan}
                    onSelect={setEditSubjectSpan}
                    highlightColor="bg-blue-200 dark:bg-blue-900"
                    disabledRange={editObjectSpan}
                  />
                </div>
              )}

              {needsObject && (
                <div className="space-y-2">
                  <Label className="text-sm font-medium">Object Words</Label>
                  <WordSelector
                    words={editingLabel.sentence?.text.split(/\s+/) || []}
                    selection={editObjectSpan}
                    onSelect={setEditObjectSpan}
                    highlightColor="bg-amber-200 dark:bg-amber-900"
                    disabledRange={editSubjectSpan}
                  />
                </div>
              )}
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditingLabel(null)}>
              Cancel
            </Button>
            <Button onClick={handleSaveEdit}>Save Changes</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation */}
      <AlertDialog open={!!deletingLabel} onOpenChange={() => setDeletingLabel(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Label</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete this label? This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleDelete} className="bg-destructive text-destructive-foreground">
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
