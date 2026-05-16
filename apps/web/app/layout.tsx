import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "English Channel",
  description: "Agent-first VoxCPM audiobook workflow"
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
