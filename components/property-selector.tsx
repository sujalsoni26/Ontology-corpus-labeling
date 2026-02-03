"use client"

import { useState } from "react"
import { Property } from "@/lib/types"
import { Button } from "@/components/ui/button"
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"
import { Badge } from "@/components/ui/badge"
import { Check, ChevronsUpDown } from "lucide-react"
import { cn } from "@/lib/utils"

interface PropertySelectorProps {
  properties: Property[]
  selectedProperty: Property | null
  onSelect: (property: Property | null) => void
}

export function PropertySelector({
  properties,
  selectedProperty,
  onSelect,
}: PropertySelectorProps) {
  const [open, setOpen] = useState(false)

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          role="combobox"
          aria-expanded={open}
          className="w-full justify-between h-auto min-h-10 py-2"
        >
          {selectedProperty ? (
            <div className="flex items-center gap-2 text-left">
              <span className="font-medium">{selectedProperty.name}</span>
              <Badge variant="secondary" className="ml-2">
                {selectedProperty.sentence_count} sentences
              </Badge>
            </div>
          ) : (
            <span className="text-muted-foreground">Select a property...</span>
          )}
          <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-[var(--radix-popover-trigger-width)] p-0" align="start">
        <Command>
          <CommandInput placeholder="Search properties..." />
          <CommandList>
            <CommandEmpty>No property found.</CommandEmpty>
            <CommandGroup>
              {properties.map((property) => (
                <CommandItem
                  key={property.id}
                  value={property.name}
                  onSelect={() => {
                    onSelect(property)
                    setOpen(false)
                  }}
                >
                  <Check
                    className={cn(
                      "mr-2 h-4 w-4",
                      selectedProperty?.id === property.id
                        ? "opacity-100"
                        : "opacity-0"
                    )}
                  />
                  <div className="flex-1">
                    <span>{property.name}</span>
                    <span className="ml-2 text-xs text-muted-foreground">
                      ({property.sentence_count} sentences)
                    </span>
                  </div>
                </CommandItem>
              ))}
            </CommandGroup>
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  )
}
