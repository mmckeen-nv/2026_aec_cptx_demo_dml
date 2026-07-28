import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Cliff House Control Plane",
  description: "Live Hermes, Rhino, Blender, and ComfyUI orchestration for the AEC Cliff House build.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
