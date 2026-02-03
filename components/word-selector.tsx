"use client"

import { cn } from "@/lib/utils"

interface WordSelectorProps {
  words: string[]
  selection: [number, number] | null
  onSelect: (span: [number, number] | null) => void
  highlightColor: string
  disabledRange?: [number, number] | null
}

export function WordSelector({
  words,
  selection,
  onSelect,
  highlightColor,
  disabledRange,
}: WordSelectorProps) {
  const handleWordClick = (index: number) => {
    // Check if clicking on a disabled word
    if (disabledRange && index >= disabledRange[0] && index <= disabledRange[1]) {
      return
    }

    if (!selection) {
      // Start new selection
      onSelect([index, index])
    } else if (selection[0] === index && selection[1] === index) {
      // Clicking the only selected word clears selection
      onSelect(null)
    } else if (index < selection[0]) {
      // Extend selection to the left
      onSelect([index, selection[1]])
    } else if (index > selection[1]) {
      // Extend selection to the right
      onSelect([selection[0], index])
    } else if (index === selection[0]) {
      // Shrink from left
      onSelect([index + 1, selection[1]])
    } else if (index === selection[1]) {
      // Shrink from right
      onSelect([selection[0], index - 1])
    } else {
      // Click in the middle - shrink to just that word
      onSelect([index, index])
    }
  }

  const isSelected = (index: number) => {
    return selection && index >= selection[0] && index <= selection[1]
  }

  const isDisabled = (index: number) => {
    return disabledRange && index >= disabledRange[0] && index <= disabledRange[1]
  }

  return (
    <div className="rounded-lg border bg-card p-4">
      <div className="flex flex-wrap gap-1.5">
        {words.map((word, index) => (
          <button
            key={index}
            onClick={() => handleWordClick(index)}
            disabled={isDisabled(index)}
            className={cn(
              "px-2 py-1 rounded text-sm transition-colors",
              isSelected(index) && highlightColor,
              isDisabled(index)
                ? "opacity-50 cursor-not-allowed bg-muted"
                : "hover:bg-muted cursor-pointer",
              !isSelected(index) && !isDisabled(index) && "bg-secondary"
            )}
          >
            {word}
          </button>
        ))}
      </div>
      {selection && (
        <p className="mt-3 text-sm text-muted-foreground">
          Selected: <span className="font-medium">{words.slice(selection[0], selection[1] + 1).join(" ")}</span>
        </p>
      )}
    </div>
  )
}
