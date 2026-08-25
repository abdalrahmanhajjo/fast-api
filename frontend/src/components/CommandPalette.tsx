import type { LucideIcon } from 'lucide-react'
import { ArrowRight } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandShortcut,
} from '@/components/ui/command'

interface CommandItemDefinition {
  to: string
  label: string
  icon: LucideIcon
}

interface CommandPaletteProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  items: CommandItemDefinition[]
}

export default function CommandPalette({ open, onOpenChange, items }: CommandPaletteProps) {
  const navigate = useNavigate()

  function navigateTo(path: string) {
    navigate(path)
    onOpenChange(false)
  }

  return (
    <CommandDialog open={open} onOpenChange={onOpenChange}>
      <CommandInput placeholder="Where do you want to go?" />
      <CommandList>
        <CommandEmpty>No matching destination.</CommandEmpty>
        <CommandGroup heading="Navigate">
          {items.map(({ to, label, icon: Icon }) => (
            <CommandItem key={to} value={label} onSelect={() => navigateTo(to)}>
              <Icon />
              <span>{label}</span>
              <CommandShortcut>
                <ArrowRight />
              </CommandShortcut>
            </CommandItem>
          ))}
        </CommandGroup>
      </CommandList>
    </CommandDialog>
  )
}
