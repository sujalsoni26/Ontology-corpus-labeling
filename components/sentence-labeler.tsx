"use client"

import { useState, useCallback } from "react"
import { Property, Sentence, LABEL_OPTIONS, LabelType } from "@/lib/types"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { Label } from "@/components/ui/label"
import { WordSelector } from "@/components/word-selector"
import { Loader2, AlertCircle, CheckCircle } from "lucide-react"

interface SentenceLabelerProps {
  sentence: Sentence
  property: Property
  onSubmit: (
    labelType: LabelType,
    subjectSpan: [number, number] | null,
    objectSpan: [number, number] | null
  ) => Promise<boolean>
}

export function SentenceLabeler({ sentence, property, onSubmit }: SentenceLabelerProps) {
  const [labelType, setLabelType] = useState<LabelType | null>(null)
  const [subjectSpan, setSubjectSpan] = useState<[number, number] | null>(null)
  const [objectSpan, setObjectSpan] = useState<[number, number] | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  const words = sentence.text.split(/\s+/)

  const validateLabel = useCallback((): string | null => {
    if (!labelType) return "Please select a label type"

    switch (labelType) {
      case "pdr":
        if (!subjectSpan) return "Please select subject words for full alignment"
        if (!objectSpan) return "Please select object words for full alignment"
        break
      case "pd":
        if (!subjectSpan) return "Please select subject words for correct domain"
        break
      case "pr":
        if (!objectSpan) return "Please select object words for correct range"
        break
      case "p":
      case "n":
        // No word selection required
        break
    }

    return null
  }, [labelType, subjectSpan, objectSpan])

  const handleSubmit = async () => {
    const validationError = validateLabel()
    if (validationError) {
      setError(validationError)
      return
    }

    setLoading(true)
    setError(null)

    const result = await onSubmit(labelType!, subjectSpan, objectSpan)

    setLoading(false)

    if (result) {
      setSuccess(true)
      setTimeout(() => {
        setSuccess(false)
        setLabelType(null)
        setSubjectSpan(null)
        setObjectSpan(null)
      }, 500)
    } else {
      setError("Failed to submit label. Please try again.")
    }
  }

  const needsSubject = labelType === "pdr" || labelType === "pd"
  const needsObject = labelType === "pdr" || labelType === "pr"

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>Label This Sentence</span>
          <Badge variant="outline">
            {sentence.label_count} label{sentence.label_count !== 1 ? "s" : ""}
          </Badge>
        </CardTitle>
        <CardDescription>
          Property: <strong>{property.name}</strong>
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="rounded-lg bg-muted p-4">
          <p className="text-lg leading-relaxed">{sentence.text}</p>
        </div>

        <div className="space-y-3">
          <Label className="text-base font-medium">Select Label Type</Label>
          <RadioGroup
            value={labelType || ""}
            onValueChange={(value) => {
              setLabelType(value as LabelType)
              setError(null)
              if (value === "p" || value === "n") {
                setSubjectSpan(null)
                setObjectSpan(null)
              }
            }}
            className="grid gap-2"
          >
            {LABEL_OPTIONS.map((option) => (
              <div key={option.value} className="flex items-center space-x-3">
                <RadioGroupItem value={option.value} id={option.value} />
                <Label
                  htmlFor={option.value}
                  className="flex-1 cursor-pointer flex items-center gap-2"
                >
                  <div className={`w-3 h-3 rounded-full ${option.color}`} />
                  <span className="font-medium">{option.label}</span>
                  <span className="text-muted-foreground text-sm">
                    - {option.description}
                  </span>
                </Label>
              </div>
            ))}
          </RadioGroup>
        </div>

        {(needsSubject || needsObject) && (
          <div className="space-y-4 pt-4 border-t">
            <p className="text-sm text-muted-foreground">
              Click on words to select them. Click again to deselect.
            </p>

            {needsSubject && (
              <div className="space-y-2">
                <Label className="text-sm font-medium">
                  Select Subject Words{" "}
                  <span className="text-muted-foreground">
                    (Domain: {property.domain_label || property.domain || "N/A"})
                  </span>
                </Label>
                <WordSelector
                  words={words}
                  selection={subjectSpan}
                  onSelect={setSubjectSpan}
                  highlightColor="bg-blue-200 dark:bg-blue-900"
                  disabledRange={objectSpan}
                />
              </div>
            )}

            {needsObject && (
              <div className="space-y-2">
                <Label className="text-sm font-medium">
                  Select Object Words{" "}
                  <span className="text-muted-foreground">
                    (Range: {property.range_label || property.range || "N/A"})
                  </span>
                </Label>
                <WordSelector
                  words={words}
                  selection={objectSpan}
                  onSelect={setObjectSpan}
                  highlightColor="bg-amber-200 dark:bg-amber-900"
                  disabledRange={subjectSpan}
                />
              </div>
            )}
          </div>
        )}

        {error && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {success && (
          <Alert className="border-green-500 bg-green-50 dark:bg-green-950">
            <CheckCircle className="h-4 w-4 text-green-600" />
            <AlertDescription className="text-green-600">
              Label submitted successfully!
            </AlertDescription>
          </Alert>
        )}

        <Button
          onClick={handleSubmit}
          disabled={!labelType || loading}
          className="w-full"
          size="lg"
        >
          {loading ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin mr-2" />
              Submitting...
            </>
          ) : (
            "Submit Label"
          )}
        </Button>
      </CardContent>
    </Card>
  )
}
