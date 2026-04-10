"use client";

/**
 * Impact Observatory | مرصد الأثر — Direction Provider
 * Syncs <html> lang/dir with Zustand language state.
 */

import { useEffect } from "react";
import { useAppStore } from "@/store/app-store";

export function DirectionProvider({ children }: { children: React.ReactNode }) {
  const language = useAppStore((s) => s.language);

  useEffect(() => {
    const html = document.documentElement;
    html.lang = language;
    html.dir = language === "ar" ? "rtl" : "ltr";
    html.classList.toggle("font-ar", language === "ar");
  }, [language]);

  return <>{children}</>;
}
