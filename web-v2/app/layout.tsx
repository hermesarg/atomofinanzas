import type { Metadata, Viewport } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Átomo Finanzas",
  description: "Las cuentas las hago yo. Las decisiones, vos.",
  applicationName: "Átomo Finanzas"
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#101114"
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  );
}
