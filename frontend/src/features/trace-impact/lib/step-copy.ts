export interface StepCopy {
  label: { en: string; ar: string };
  title: { en: string; ar: string };
  subtitle: { en: string; ar: string };
}

export const STEP_COPY: StepCopy[] = [
  {
    label: { en: "Signal", ar: "الإشارة" },
    title: { en: "Macroeconomic Intelligence for the GCC", ar: "الذكاء الاقتصادي الكلي لدول مجلس التعاون" },
    subtitle: {
      en: "Regional macro conditions are shifting. Energy-driven stress has elevated systemic risk across six GCC economies.",
      ar: "تتحول الظروف الاقتصادية الكلية الإقليمية. أفضى الضغط الناجم عن قطاع الطاقة إلى ارتفاع المخاطر المنهجية عبر اقتصادات دول الخليج الست.",
    },
  },
  {
    label: { en: "Impact", ar: "الأثر" },
    title: { en: "Strait of Hormuz Disruption", ar: "اضطراب مضيق هرمز" },
    subtitle: {
      en: "A maritime disruption cuts 60% of Gulf oil transit, triggering systemic stress across six GCC economies.",
      ar: "اضطراب بحري يقطع 60٪ من عبور النفط الخليجي، مما يتسبب في ضغط منهجي عبر ست اقتصادات خليجية.",
    },
  },
  {
    label: { en: "Transmission", ar: "مسار الانتقال" },
    title: { en: "How the Shock Spreads", ar: "كيف تنتشر الصدمة" },
    subtitle: {
      en: "Stress moves from energy pricing through banking liquidity, insurance exposure, and fintech settlement chains.",
      ar: "ينتقل الضغط من تسعير الطاقة عبر سيولة البنوك وتعرض التأمين وسلاسل تسوية التقنية المالية.",
    },
  },
  {
    label: { en: "Exposure", ar: "التعرض" },
    title: { en: "Who Bears the Impact", ar: "من يتحمل الأثر" },
    subtitle: {
      en: "All six Gulf economies face simultaneous pressure across energy, banking, and trade sectors.",
      ar: "ست اقتصادات خليجية تواجه ضغطاً متزامناً عبر قطاعات الطاقة والمصارف والتجارة.",
    },
  },
  {
    label: { en: "Decision", ar: "القرار" },
    title: { en: "Act or Absorb", ar: "التدخل أو الاستيعاب" },
    subtitle: {
      en: "A 71-hour decision window separates a $4.3B outcome from a $4.9B loss trajectory.",
      ar: "نافذة قرار 71 ساعة تفصل بين نتيجة 4.3 مليار دولار ومسار خسارة 4.9 مليار دولار.",
    },
  },
  {
    label: { en: "Outcome", ar: "النتيجة" },
    title: { en: "What Coordinated Action Achieves", ar: "ما يحققه التدخل المنسق" },
    subtitle: {
      en: "Coordinated regional response contains damage within 72 hours and preserves $600M in avoided losses.",
      ar: "الاستجابة الإقليمية المنسقة تحتوي الأضرار خلال 72 ساعة وتحافظ على 600 مليون دولار من الخسائر المتجنبة.",
    },
  },
];

export const EXPERIENCE_COPY = {
  ctaLabel: { en: "Trace Impact", ar: "تتبع الأثر" },
  ctaSubLabel: {
    en: "Guided Scenario Walkthrough",
    ar: "جولة إرشادية للسيناريو",
  },
  exitLabel: { en: "Standard View", ar: "العرض التقليدي" },
  toggleLabel: { en: "Trace Impact", ar: "تتبع الأثر" },
  next: { en: "Next", ar: "التالي" },
  prev: { en: "Previous", ar: "السابق" },
  finish: { en: "View Decision Room", ar: "غرفة القرار" },
  keyboardHint: { en: "← → to navigate", ar: "← → للتنقل" },
};
