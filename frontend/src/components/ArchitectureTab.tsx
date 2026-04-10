"use client";

/**
 * Impact Observatory | مرصد الأثر — Architecture Tab (Layer 4)
 *
 * Layered architecture visualization: Input → Simulation → Risk Models →
 * Decision Engine → Output. Plain language per layer. No code references.
 * No developer terminology. Expandable from a trigger button.
 */

import React, { useState } from "react";
import type { Language } from "@/types/observatory";

interface ArchLayer {
  id: string;
  label: string;
  label_ar: string;
  description: string;
  description_ar: string;
  color: string;
  icon: string;
}

const labels: Record<Language, Record<string, string>> = {
  en: {
    trigger: "System Architecture",
    hide: "Hide Architecture",
    title: "How the System Works",
    subtitle: "Five layers transform a scenario into actionable decisions",
  },
  ar: {
    trigger: "بنية النظام",
    hide: "إخفاء البنية",
    title: "كيف يعمل النظام",
    subtitle: "خمس طبقات تحول السيناريو إلى قرارات قابلة للتنفيذ",
  },
};

const LAYERS: ArchLayer[] = [
  {
    id: "input",
    label: "Scenario Input",
    label_ar: "مدخلات السيناريو",
    description: "A geopolitical or economic event is defined with severity, affected sectors, and time horizon. The system validates inputs and configures the simulation parameters.",
    description_ar: "يتم تحديد حدث جيوسياسي أو اقتصادي بالشدة والقطاعات المتأثرة والأفق الزمني. يتحقق النظام من المدخلات ويضبط معاملات المحاكاة.",
    color: "border-l-blue-500 bg-blue-50/50",
    icon: "1",
  },
  {
    id: "simulation",
    label: "Physics Simulation",
    label_ar: "محاكاة فيزيائية",
    description: "The system models how disruptions propagate through interconnected economic networks — measuring flow, capacity, and bottleneck effects across supply chains and financial corridors.",
    description_ar: "يحاكي النظام كيف تنتشر الاضطرابات عبر الشبكات الاقتصادية المترابطة — قياس التدفق والسعة وتأثيرات الاختناق عبر سلاسل التوريد والممرات المالية.",
    color: "border-l-amber-500 bg-amber-50/50",
    icon: "2",
  },
  {
    id: "risk",
    label: "Risk Assessment",
    label_ar: "تقييم المخاطر",
    description: "Financial losses, banking liquidity stress, insurance exposure, and fintech payment disruptions are quantified. Each entity receives a composite risk score calibrated to GCC market conditions.",
    description_ar: "يتم قياس الخسائر المالية وضغط السيولة البنكية والتعرض التأميني واضطرابات مدفوعات الفنتك. يحصل كل كيان على درجة مخاطر مركبة معايرة لأسواق الخليج.",
    color: "border-l-red-500 bg-red-50/50",
    icon: "3",
  },
  {
    id: "decision",
    label: "Decision Engine",
    label_ar: "محرك القرارات",
    description: "A multi-objective optimization identifies the top 3 priority actions — balancing urgency, financial value, regulatory risk, feasibility, and time sensitivity to produce executive-ready recommendations.",
    description_ar: "يحدد تحسين متعدد الأهداف أهم 3 إجراءات ذات أولوية — بموازنة الإلحاح والقيمة المالية والمخاطر التنظيمية والجدوى والحساسية الزمنية لإنتاج توصيات تنفيذية.",
    color: "border-l-violet-500 bg-violet-50/50",
    icon: "4",
  },
  {
    id: "output",
    label: "Executive Output",
    label_ar: "المخرجات التنفيذية",
    description: "Results are presented as an auditable decision brief — with confidence scores, trace IDs, and plain-language explanations. Every number can be traced back to its source equation.",
    description_ar: "تُقدَّم النتائج كموجز قرار قابل للتدقيق — مع درجات الثقة ومعرفات التتبع والشروحات بلغة واضحة. يمكن تتبع كل رقم إلى معادلته المصدرية.",
    color: "border-l-emerald-500 bg-emerald-50/50",
    icon: "5",
  },
];

export default function ArchitectureTab({
  lang = "en",
}: {
  lang?: Language;
}) {
  const [open, setOpen] = useState(false);
  const t = labels[lang];
  const isRTL = lang === "ar";

  return (
    <div className={`${isRTL ? "font-ar" : "font-sans"}`} dir={isRTL ? "rtl" : "ltr"}>
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 text-xs font-medium text-io-accent hover:text-io-accent/80 transition-colors mb-2"
      >
        {open ? t.hide : t.trigger}
        <span className="text-[10px]">{open ? "▲" : "▼"}</span>
      </button>

      {open && (
        <div className="bg-io-surface border border-io-border rounded-xl p-5 shadow-sm">
          <div className="mb-5">
            <p className="text-sm font-semibold text-io-primary">{t.title}</p>
            <p className="text-xs text-io-secondary mt-0.5">{t.subtitle}</p>
          </div>

          <div className="space-y-3">
            {LAYERS.map((layer, i) => (
              <div key={layer.id}>
                <div
                  className={`flex items-start gap-4 p-4 rounded-lg border-l-4 border border-io-border/50 ${layer.color}`}
                >
                  {/* Step number */}
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-white border-2 border-io-border flex items-center justify-center text-sm font-bold text-io-primary shadow-sm">
                    {layer.icon}
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-semibold text-io-primary">
                      {isRTL ? layer.label_ar : layer.label}
                    </p>
                    <p className="text-xs text-io-secondary mt-1 leading-relaxed">
                      {isRTL ? layer.description_ar : layer.description}
                    </p>
                  </div>
                </div>
                {/* Connector */}
                {i < LAYERS.length - 1 && (
                  <div className="flex justify-center py-1">
                    <div className="w-px h-4 bg-io-border" />
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
