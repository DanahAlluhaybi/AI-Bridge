import type { ButtonHTMLAttributes } from "react";

type Variant = "primary" | "secondary" | "ghost" | "danger-ghost";

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
}

const VARIANT_CLASS: Record<Variant, string> = {
  primary: "btn-primary",
  secondary: "btn-secondary",
  ghost: "btn-ghost",
  "danger-ghost": "btn-danger-ghost",
};

// Every clickable action in the product goes through this component,
// so a button always has the same padding, radius, and weight
// regardless of which page it's on.
export default function Button({
  variant = "primary",
  className = "",
  ...props
}: Props) {
  return <button className={`${VARIANT_CLASS[variant]} ${className}`} {...props} />;
}
