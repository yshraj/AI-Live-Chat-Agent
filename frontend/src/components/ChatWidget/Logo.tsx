import "./Logo.css";

interface LogoProps {
  size?: "small" | "medium" | "large";
  className?: string;
}

export function Logo({ size = "medium", className = "" }: LogoProps) {
  return (
    <div className={`logo logo--${size} ${className}`}>
      <div className="logo__circle"></div>
    </div>
  );
}

