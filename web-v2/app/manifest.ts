import type { MetadataRoute } from "next";

export const dynamic = "force-static";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Átomo Finanzas",
    short_name: "Átomo",
    description: "Las cuentas las hago yo. Las decisiones, vos.",
    start_url: "/",
    display: "standalone",
    background_color: "#0f1115",
    theme_color: "#101114",
    orientation: "portrait-primary",
    icons: [
      {
        src: "/atomo_favicon.png",
        sizes: "512x512",
        type: "image/png",
        purpose: "any"
      }
    ]
  };
}
