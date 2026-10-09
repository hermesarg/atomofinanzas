import type { Metadata, Viewport } from "next";
import "./globals.css";
import { FinanceProvider } from "@/lib/store";

export const metadata: Metadata = {
  title: "Átomo Finanzas",
  description: "Las cuentas las hago yo. Las decisiones, vos.",
  applicationName: "Átomo Finanzas",
  manifest: "/manifest.webmanifest"
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#101114"
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="es">
      <body>
        <FinanceProvider>{children}</FinanceProvider>
      </body>
    </html>
  );
}
