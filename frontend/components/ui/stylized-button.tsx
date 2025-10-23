import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const stylizedButtonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium transition-all focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        primary: "bg-primary text-primary-foreground shadow hover:bg-primary/90",
        outline: "border border-input bg-background shadow-sm hover:bg-accent hover:text-accent-foreground",
        glow: "bg-gradient-to-r from-primary to-accent text-primary-foreground shadow-lg hover:shadow-xl hover:scale-105",
      },
      size: {
        default: "h-9 px-4 py-2",
        sm: "h-8 rounded-md px-3 text-xs",
        lg: "h-10 rounded-md px-8",
        icon: "h-9 w-9",
      },
    },
    defaultVariants: {
      variant: "primary",
      size: "default",
    },
  },
)

export interface StylizedButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof stylizedButtonVariants> {
  asChild?: boolean
  iconRight?: React.ReactNode
  withIcon?: boolean
}

const StylizedButton = React.forwardRef<HTMLButtonElement, StylizedButtonProps>(
  ({ className, variant, size, asChild = false, iconRight, withIcon, children, ...props }, ref) => {
    const Comp = asChild ? Slot : "button"
    return (
      <Comp className={cn(stylizedButtonVariants({ variant, size, className }))} ref={ref} {...props}>
        {children}
        {iconRight && (
          <span className={cn("transition-transform", withIcon && "group-hover:translate-x-0.5")}>{iconRight}</span>
        )}
      </Comp>
    )
  },
)
StylizedButton.displayName = "StylizedButton"

export { StylizedButton, stylizedButtonVariants }
