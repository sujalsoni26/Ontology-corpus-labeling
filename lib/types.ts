export interface Property {
  id: string
  name: string
  domain: string | null
  range: string | null
  domain_label: string | null
  range_label: string | null
  iri: string | null
  sentence_count: number
  created_at: string
}

export interface Sentence {
  id: string
  property_id: string
  text: string
  label_count: number
  created_at: string
}

export interface Label {
  id: string
  user_id: string
  sentence_id: string
  property_id: string
  label_type: "pdr" | "pd" | "pr" | "p" | "n"
  subject_start: number | null
  subject_end: number | null
  object_start: number | null
  object_end: number | null
  created_at: string
  updated_at: string
}

export interface LabelWithDetails extends Label {
  sentence: Sentence
  property: Property
}

export type LabelType = "pdr" | "pd" | "pr" | "p" | "n"

export const LABEL_OPTIONS: { value: LabelType; label: string; description: string; color: string }[] = [
  {
    value: "pdr",
    label: "Full Alignment (pdr)",
    description: "Property + Domain + Range all correct",
    color: "bg-green-500",
  },
  {
    value: "pd",
    label: "Correct Domain (pd)",
    description: "Property + Domain correct, Range incorrect",
    color: "bg-blue-500",
  },
  {
    value: "pr",
    label: "Correct Range (pr)",
    description: "Property + Range correct, Domain incorrect",
    color: "bg-amber-500",
  },
  {
    value: "p",
    label: "Incorrect D&R (p)",
    description: "Property correct, Domain and Range incorrect",
    color: "bg-orange-500",
  },
  {
    value: "n",
    label: "No Alignment (n)",
    description: "No alignment with property",
    color: "bg-red-500",
  },
]
