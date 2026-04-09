"""
Impact Observatory | مرصد الأثر
Executive Narrative Engine — transforms SimulateResponse into structured
intelligence briefs.

Architecture Layer: Narrative (sits above SimulationEngine, below API)
Dependencies: simulation_schemas (SimulateResponse), explainability, config
No LLM: all narratives are deterministic, template-based, bilingual.

Output contract:
  Signal → Propagation → Exposure → Decision → Outcome
"""
from __future__ import annotations

import math
from typing import Any

from src.utils import clamp, format_loss_usd, classify_stress


# ─────────────────────────────────────────────────────────────────────────────
# Scenario context library — enriches scenario_id with strategic context
# ─────────────────────────────────────────────────────────────────────────────

_SCENARIO_CONTEXT: dict[str, dict[str, str]] = {
    "hormuz_chokepoint_disruption": {
        "signal": "Maritime surveillance detected anomalous vessel movements and potential obstruction near the Strait of Hormuz.",
        "signal_ar": "رصدت المراقبة البحرية تحركات غير طبيعية للسفن واحتمال عرقلة بالقرب من مضيق هرمز.",
        "root_cause": "Partial blockage or militarized escalation restricting tanker transit through the world's most critical oil chokepoint.",
        "root_cause_ar": "انسداد جزئي أو تصعيد عسكري يُقيّد عبور الناقلات عبر أهم نقطة اختناق نفطية في العالم.",
        "strategic_context": "21M barrels/day flow through Hormuz — 30% of global seaborne oil. Disruption triggers immediate energy price spikes, shipping rerouting, and cascading financial stress across GCC economies.",
        "strategic_context_ar": "يمر 21 مليون برميل يومياً عبر هرمز — 30% من النفط المنقول بحراً عالمياً. يُحدث الاضطراب ارتفاعات فورية في أسعار الطاقة وإعادة توجيه الشحن وضغوط مالية متتالية عبر اقتصادات الخليج.",
    },
    "hormuz_full_closure": {
        "signal": "Intelligence indicates complete cessation of maritime transit through the Strait of Hormuz due to military escalation.",
        "signal_ar": "تشير المعلومات الاستخبارية إلى توقف كامل للعبور البحري عبر مضيق هرمز بسبب التصعيد العسكري.",
        "root_cause": "Full military closure of the strait, halting all oil tanker and LNG carrier transit.",
        "root_cause_ar": "إغلاق عسكري كامل للمضيق يوقف جميع عمليات عبور ناقلات النفط وناقلات الغاز المسال.",
        "strategic_context": "Extreme scenario with catastrophic supply chain implications. GCC GDP at immediate risk with potential $8.5B+ exposure.",
        "strategic_context_ar": "سيناريو متطرف بتداعيات كارثية على سلسلة التوريد. الناتج المحلي الإجمالي الخليجي في خطر فوري مع تعرض محتمل يتجاوز 8.5 مليار دولار.",
    },
    "uae_banking_crisis": {
        "signal": "Early warning indicators show rising NPL ratios and interbank lending spreads in UAE financial institutions.",
        "signal_ar": "تُظهر مؤشرات الإنذار المبكر ارتفاع نسب القروض المتعثرة وفروق الإقراض بين البنوك في المؤسسات المالية الإماراتية.",
        "root_cause": "Systemic credit deterioration across UAE banking sector, potentially triggered by real estate exposure or sovereign credit event.",
        "root_cause_ar": "تدهور ائتماني نظامي عبر القطاع المصرفي الإماراتي، ناجم محتملاً عن التعرض العقاري أو حدث ائتماني سيادي.",
        "strategic_context": "UAE banking assets exceed $1T. DIFC is the GCC's financial gravity center. Contagion propagates through interbank markets, payment rails, and cross-border lending.",
        "strategic_context_ar": "تتجاوز أصول البنوك الإماراتية تريليون دولار. مركز دبي المالي الدولي هو مركز الجاذبية المالية الخليجي. تنتشر العدوى عبر أسواق ما بين البنوك وقنوات الدفع والإقراض العابر للحدود.",
    },
    "gcc_cyber_attack": {
        "signal": "CERT-GCC detected coordinated intrusion attempts targeting SWIFT gateway nodes and payment processing infrastructure.",
        "signal_ar": "رصد فريق الاستجابة للطوارئ محاولات اختراق منسقة تستهدف عقد بوابة سويفت والبنية التحتية لمعالجة المدفوعات.",
        "root_cause": "State-sponsored or advanced persistent threat (APT) targeting GCC financial infrastructure to disrupt settlement and payment systems.",
        "root_cause_ar": "تهديد مدعوم من دولة أو تهديد متقدم مستمر يستهدف البنية التحتية المالية الخليجية لتعطيل أنظمة التسوية والمدفوعات.",
        "strategic_context": "GCC payment systems process $800B+ annually through interconnected SWIFT and RTGS nodes. A targeted cyber disruption can freeze cross-border settlements within hours.",
        "strategic_context_ar": "تعالج أنظمة الدفع الخليجية أكثر من 800 مليار دولار سنوياً عبر عقد سويفت وRTGS المترابطة. يمكن للاختراق المستهدف تجميد التسويات العابرة للحدود في غضون ساعات.",
    },
    "saudi_oil_shock": {
        "signal": "Aramco production monitoring reports abrupt output reduction from primary processing facilities.",
        "signal_ar": "تُبلغ مراقبة إنتاج أرامكو عن انخفاض مفاجئ في الإنتاج من مرافق المعالجة الرئيسية.",
        "root_cause": "Major disruption to Saudi Aramco operations — facility damage, sabotage, or forced production curtailment affecting 12M bpd capacity.",
        "root_cause_ar": "اضطراب كبير في عمليات أرامكو السعودية — أضرار في المنشآت أو تخريب أو تقليص قسري للإنتاج يؤثر على طاقة 12 مليون برميل يومياً.",
        "strategic_context": "Saudi Arabia is the world's largest oil exporter. Production shock immediately impacts global energy prices, GCC fiscal balances, and downstream industries.",
        "strategic_context_ar": "المملكة العربية السعودية أكبر مُصدّر للنفط في العالم. صدمة الإنتاج تؤثر فوراً على أسعار الطاقة العالمية والموازين المالية الخليجية والصناعات التابعة.",
    },
    "qatar_lng_disruption": {
        "signal": "LNG loading terminals at Ras Laffan report operational shutdown affecting scheduled cargo dispatch.",
        "signal_ar": "تُبلغ محطات تحميل الغاز المسال في رأس لفان عن توقف تشغيلي يؤثر على شحنات البضائع المجدولة.",
        "root_cause": "Disruption to Qatar's 77Mtpa LNG export capacity — the world's largest — from facility failure, embargo, or force majeure.",
        "root_cause_ar": "اضطراب في طاقة تصدير الغاز المسال القطرية البالغة 77 مليون طن سنوياً — الأكبر عالمياً — بسبب عطل في المنشآت أو حظر أو قوة قاهرة.",
        "strategic_context": "Qatar supplies 25% of global LNG. Disruption triggers European and Asian energy crises, shipping rerouting, and cascading price volatility.",
        "strategic_context_ar": "توفر قطر 25% من الغاز المسال العالمي. يُحدث الاضطراب أزمات طاقة أوروبية وآسيوية وإعادة توجيه الشحن وتقلبات سعرية متتالية.",
    },
    "bahrain_sovereign_stress": {
        "signal": "Credit rating agencies signal downgrade watch on Bahrain sovereign debt; CDS spreads widening sharply.",
        "signal_ar": "تُشير وكالات التصنيف الائتماني إلى مراقبة خفض التصنيف على الدين السيادي البحريني؛ فروق أسعار CDS تتوسع بحدة.",
        "root_cause": "Fiscal deterioration and rising debt-to-GDP ratio eroding Bahrain's sovereign creditworthiness.",
        "root_cause_ar": "التدهور المالي وارتفاع نسبة الدين إلى الناتج المحلي الإجمالي يُضعف الجدارة الائتمانية السيادية للبحرين.",
        "strategic_context": "Bahrain Financial Harbour hosts the GCC reinsurance hub. Sovereign stress cascades through banking sector solvency and regional confidence.",
        "strategic_context_ar": "يستضيف مرسى البحرين المالي مركز إعادة التأمين الخليجي. الضغط السيادي ينتقل عبر ملاءة القطاع المصرفي والثقة الإقليمية.",
    },
    "kuwait_fiscal_shock": {
        "signal": "Kuwait National Assembly budget reports reveal structural fiscal deficit exceeding emergency reserve drawdown thresholds.",
        "signal_ar": "تكشف تقارير ميزانية مجلس الأمة الكويتي عن عجز مالي هيكلي يتجاوز عتبات السحب من الاحتياطي الطارئ.",
        "root_cause": "Sustained low oil prices combined with rigid fiscal structure drain Kuwait's sovereign buffers.",
        "root_cause_ar": "انخفاض مستمر في أسعار النفط مع هيكل مالي جامد يستنزف احتياطيات الكويت السيادية.",
        "strategic_context": "Kuwait's economy is 90% oil-dependent. Fiscal shock impairs public spending, banking liquidity, and investment pipeline.",
        "strategic_context_ar": "يعتمد اقتصاد الكويت على النفط بنسبة 90%. الصدمة المالية تُضعف الإنفاق العام وسيولة البنوك ومسار الاستثمار.",
    },
    "oman_port_closure": {
        "signal": "Port authority declares force majeure at Salalah and Sohar, suspending container and bulk cargo operations.",
        "signal_ar": "تعلن سلطة الميناء حالة القوة القاهرة في صلالة وصحار، وتعلق عمليات الحاويات والبضائع السائبة.",
        "root_cause": "Physical closure of Oman's primary trade infrastructure — cyclone, conflict, or critical equipment failure.",
        "root_cause_ar": "إغلاق مادي للبنية التجارية الرئيسية لعُمان — إعصار أو صراع أو عطل في المعدات الحيوية.",
        "strategic_context": "Salalah is a key Indian Ocean transshipment hub. Closure diverts traffic, increases freight rates, and delays GCC-Asia trade flows.",
        "strategic_context_ar": "صلالة مركز رئيسي لإعادة الشحن في المحيط الهندي. الإغلاق يحوّل حركة المرور ويرفع أسعار الشحن ويؤخر تدفقات التجارة بين الخليج وآسيا.",
    },
    "red_sea_trade_corridor_instability": {
        "signal": "Maritime intelligence reports escalating attacks on commercial vessels transiting the Bab el-Mandeb strait.",
        "signal_ar": "تفيد الاستخبارات البحرية بتصاعد الهجمات على السفن التجارية العابرة لمضيق باب المندب.",
        "root_cause": "Houthi or non-state actor attacks on Red Sea shipping lanes, forcing rerouting around the Cape of Good Hope.",
        "root_cause_ar": "هجمات الحوثيين أو جهات فاعلة غير حكومية على ممرات الشحن في البحر الأحمر، مما يفرض إعادة التوجيه حول رأس الرجاء الصالح.",
        "strategic_context": "12% of global trade passes through the Red Sea. Disruption adds 10-14 days to Europe-Asia routes, inflating freight and insurance costs.",
        "strategic_context_ar": "يمر 12% من التجارة العالمية عبر البحر الأحمر. يضيف الاضطراب 10-14 يوماً لمسارات أوروبا-آسيا، مما يرفع تكاليف الشحن والتأمين.",
    },
    "energy_market_volatility_shock": {
        "signal": "OPEC+ emergency session convened as benchmark crude prices breach extreme volatility thresholds.",
        "signal_ar": "انعقاد جلسة طوارئ أوبك+ مع اختراق أسعار النفط القياسية عتبات التقلب الشديد.",
        "root_cause": "Multi-source energy price shock from geopolitical tension, demand destruction, or speculative attack on GCC energy commodities.",
        "root_cause_ar": "صدمة أسعار طاقة متعددة المصادر من التوتر الجيوسياسي أو تدمير الطلب أو هجوم مضاربي على سلع الطاقة الخليجية.",
        "strategic_context": "GCC economies derive 40-90% of fiscal revenue from hydrocarbons. Extreme price volatility destabilizes budgets, currencies, and investment plans.",
        "strategic_context_ar": "تستمد اقتصادات الخليج 40-90% من إيراداتها المالية من المحروقات. التقلب الشديد في الأسعار يزعزع الميزانيات والعملات وخطط الاستثمار.",
    },
    "regional_liquidity_stress_event": {
        "signal": "Interbank overnight rates spike across GCC markets; central bank repo windows see unprecedented demand.",
        "signal_ar": "ارتفاع حاد في أسعار الفائدة بين البنوك لليلة واحدة عبر أسواق الخليج؛ طلب غير مسبوق على نوافذ الريبو بالبنوك المركزية.",
        "root_cause": "Synchronized liquidity withdrawal across GCC banking systems triggered by external capital flight or domestic confidence crisis.",
        "root_cause_ar": "سحب متزامن للسيولة عبر الأنظمة المصرفية الخليجية بسبب هروب رؤوس الأموال الخارجية أو أزمة ثقة محلية.",
        "strategic_context": "GCC interbank markets are deeply interconnected. Liquidity stress cascades through payment systems, trade finance, and credit markets within 48 hours.",
        "strategic_context_ar": "أسواق ما بين البنوك الخليجية مترابطة بعمق. ضغوط السيولة تنتقل عبر أنظمة الدفع وتمويل التجارة وأسواق الائتمان خلال 48 ساعة.",
    },
    "critical_port_throughput_disruption": {
        "signal": "Automated port monitoring systems report simultaneous throughput collapse at Jebel Ali, Khalifa, and King Abdul Aziz ports.",
        "signal_ar": "تُبلغ أنظمة مراقبة الموانئ الآلية عن انهيار متزامن في الإنتاجية في موانئ جبل علي وخليفة والملك عبدالعزيز.",
        "root_cause": "Multi-port operational failure from coordinated disruption, systemic equipment failure, or labor action.",
        "root_cause_ar": "عطل تشغيلي متعدد الموانئ من اضطراب منسق أو عطل نظامي في المعدات أو إضراب عمالي.",
        "strategic_context": "These three ports handle 65% of GCC container throughput. Simultaneous disruption collapses import/export capacity.",
        "strategic_context_ar": "تتعامل هذه الموانئ الثلاثة مع 65% من إنتاجية حاويات الخليج. الاضطراب المتزامن يُنهي القدرة على الاستيراد والتصدير.",
    },
    "financial_infrastructure_cyber_disruption": {
        "signal": "SOC teams across GCC financial institutions report coordinated DDoS and intrusion attempts on core banking and payment systems.",
        "signal_ar": "تُبلغ فرق مراكز عمليات الأمن عبر المؤسسات المالية الخليجية عن هجمات DDoS منسقة ومحاولات اختراق على الأنظمة المصرفية الأساسية وأنظمة الدفع.",
        "root_cause": "Targeted cyber campaign against GCC fintech and payment infrastructure — SWIFT nodes, digital payment rails, settlement systems.",
        "root_cause_ar": "حملة إلكترونية مستهدفة ضد البنية التحتية للتقنية المالية والمدفوعات الخليجية — عقد سويفت وقنوات الدفع الرقمي وأنظمة التسوية.",
        "strategic_context": "Financial infrastructure forms the nervous system of GCC economies. Cyber disruption can cascade from payment delays to full settlement failure.",
        "strategic_context_ar": "البنية التحتية المالية تشكل الجهاز العصبي لاقتصادات الخليج. الاختراق الإلكتروني يمكن أن يتصاعد من تأخيرات الدفع إلى فشل كامل في التسوية.",
    },
}

# Fallback for unknown scenarios
_DEFAULT_CONTEXT: dict[str, str] = {
    "signal": "Monitoring systems have detected an emerging risk event affecting GCC financial infrastructure.",
    "signal_ar": "رصدت أنظمة المراقبة حدث خطر ناشئ يؤثر على البنية التحتية المالية الخليجية.",
    "root_cause": "Systemic disruption originating from an identified scenario trigger within the GCC economic network.",
    "root_cause_ar": "اضطراب نظامي ناشئ عن مُحفّز سيناريو محدد ضمن الشبكة الاقتصادية الخليجية.",
    "strategic_context": "The GCC financial network is deeply interconnected. Events propagate through banking, energy, maritime, and digital payment channels.",
    "strategic_context_ar": "الشبكة المالية الخليجية مترابطة بعمق. تنتشر الأحداث عبر القنوات المصرفية والطاقة والملاحة البحرية والمدفوعات الرقمية.",
}


# ─────────────────────────────────────────────────────────────────────────────
# Sector narrative templates
# ─────────────────────────────────────────────────────────────────────────────

_SECTOR_NARRATIVES: dict[str, dict[str, str]] = {
    "banking": {
        "why_affected": "Banking is exposed through direct counterparty credit risk, interbank lending contagion, and mark-to-market losses on correlated assets. When liquidity tightens, deposit outflow accelerates and lending capacity contracts — amplifying the initial shock across the real economy.",
        "why_affected_ar": "يتعرض القطاع المصرفي من خلال مخاطر ائتمان الطرف المقابل المباشر وعدوى الإقراض بين البنوك وخسائر القيمة العادلة على الأصول المترابطة. عندما تتشدد السيولة يتسارع تدفق الودائع الخارجة وتنكمش القدرة الإقراضية — مما يضخّم الصدمة الأولية عبر الاقتصاد الحقيقي.",
        "what_happens_next": "Expect interbank rate spikes within 24-48 hours. Central bank repo windows will see elevated demand. Credit committees will freeze new lending approvals. Consumer and SME sectors feel secondary effects within 5-7 days.",
        "what_happens_next_ar": "توقع ارتفاعات في أسعار الفائدة بين البنوك خلال 24-48 ساعة. ستشهد نوافذ الريبو بالبنوك المركزية طلباً مرتفعاً. ستُجمّد لجان الائتمان الموافقات على الإقراض الجديد. يشعر قطاعا المستهلك والمنشآت الصغيرة بالآثار الثانوية خلال 5-7 أيام.",
    },
    "insurance": {
        "why_affected": "Insurance responds through claims surge amplification — when physical or financial disruption triggers policyholder losses, claim frequency and severity spike simultaneously. Reserve adequacy erodes, loss ratios deteriorate, and reinsurance treaty thresholds may be breached.",
        "why_affected_ar": "يستجيب التأمين من خلال تضخيم موجة المطالبات — عندما يُحدث الاضطراب المادي أو المالي خسائر لحاملي وثائق التأمين، ترتفع وتيرة المطالبات وشدتها في آن واحد. تتآكل كفاية الاحتياطيات وتتدهور نسب الخسارة وقد تُخترق عتبات معاهدات إعادة التأمين.",
        "what_happens_next": "Claims processing backlogs will build within 48-72 hours. Combined ratios will breach 100% for affected lines. IFRS 17 risk adjustments will be triggered, requiring immediate actuarial revaluation. Reinsurers will reassess GCC treaty capacity.",
        "what_happens_next_ar": "ستتراكم تأخيرات معالجة المطالبات خلال 48-72 ساعة. ستتجاوز النسب المركبة 100% للخطوط المتأثرة. ستُفعَّل تعديلات المخاطر وفق IFRS 17، مما يتطلب إعادة تقييم اكتواري فوري. سيُعيد مُعيدو التأمين تقييم قدرة معاهدات الخليج.",
    },
    "fintech": {
        "why_affected": "Fintech and digital payments are vulnerable because modern GCC financial infrastructure routes transactions through centralized SWIFT and RTGS nodes. Settlement delays cascade: when one node queues, downstream processors back up, API timeouts multiply, and cross-border corridors fail.",
        "why_affected_ar": "التقنية المالية والمدفوعات الرقمية عرضة للخطر لأن البنية التحتية المالية الخليجية الحديثة توجّه المعاملات عبر عقد مركزية لسويفت وRTGS. تتتالى تأخيرات التسوية: عندما تتأخر عقدة واحدة يتراكم الحمل على المعالجات التالية وتتضاعف أوقات انتهاء واجهة API وتفشل الممرات العابرة للحدود.",
        "what_happens_next": "Real-time payment systems (AANI, mada) will show latency degradation within hours. Settlement queues will build. Cross-border remittance corridors may suspend operations. Merchant payment acceptance rates will decline.",
        "what_happens_next_ar": "ستُظهر أنظمة الدفع الفوري (AANI، مدى) تدهوراً في زمن الاستجابة خلال ساعات. ستتراكم قوائم التسوية. قد تعلّق ممرات التحويلات العابرة للحدود عملياتها. ستنخفض معدلات قبول مدفوعات التجار.",
    },
    "energy": {
        "why_affected": "Energy sector disruption propagates through supply curtailment — when production facilities, pipelines, or export terminals are impacted, physical supply contracts fail to deliver, spot prices spike, and downstream industries face input cost shocks.",
        "why_affected_ar": "ينتشر اضطراب قطاع الطاقة من خلال تقليص العرض — عندما تتأثر مرافق الإنتاج أو خطوط الأنابيب أو محطات التصدير، تفشل عقود التوريد المادي في التسليم وترتفع الأسعار الفورية وتواجه الصناعات التابعة صدمات في تكاليف المدخلات.",
        "what_happens_next": "Spot energy prices will react within hours. Long-term supply contracts will invoke force majeure clauses. Downstream petrochemical and manufacturing sectors will face margin compression within days.",
        "what_happens_next_ar": "ستتفاعل أسعار الطاقة الفورية خلال ساعات. ستستدعي عقود التوريد طويلة الأجل بنود القوة القاهرة. ستواجه قطاعات البتروكيماويات والتصنيع انضغاطاً في الهوامش خلال أيام.",
    },
    "maritime": {
        "why_affected": "Maritime disruption creates immediate physical bottlenecks — vessel queuing, port congestion, and rerouting delays compound exponentially. Every day of port closure or chokepoint obstruction multiplies backlog costs and forces expensive alternative routing.",
        "why_affected_ar": "يُحدث الاضطراب البحري اختناقات مادية فورية — تتراكم طوابير السفن وازدحام الموانئ وتأخيرات إعادة التوجيه بشكل أسي. كل يوم إغلاق ميناء أو عرقلة نقطة اختناق يُضاعف تكاليف التأخير ويفرض توجيهاً بديلاً مكلفاً.",
        "what_happens_next": "Vessel queues will form within 24 hours. Freight rates will spike 30-200% depending on severity. Marine insurance premiums will be repriced. Container availability will tighten across the region.",
        "what_happens_next_ar": "ستتشكل طوابير السفن خلال 24 ساعة. سترتفع أسعار الشحن 30-200% حسب الشدة. سيُعاد تسعير أقساط التأمين البحري. سيشتد نقص الحاويات في المنطقة.",
    },
    "logistics": {
        "why_affected": "Logistics chains operate on just-in-time principles with minimal buffer stock. Disruption at any node — port, warehouse, transport corridor — creates cascading delays that multiply through the supply chain, with each hand-off amplifying the original delay.",
        "why_affected_ar": "تعمل سلاسل اللوجستيات على مبادئ التوريد الفوري مع حد أدنى من المخزون الاحتياطي. الاضطراب في أي عقدة — ميناء أو مستودع أو ممر نقل — يُحدث تأخيرات متتالية تتضاعف عبر سلسلة التوريد.",
        "what_happens_next": "Delivery timelines will extend by 2-5x. Cold chain and perishable goods face immediate spoilage risk. Inventory costs spike as firms shift to emergency stockpiling.",
        "what_happens_next_ar": "ستمتد مواعيد التسليم بمقدار 2-5 أضعاف. تواجه سلسلة التبريد والبضائع القابلة للتلف خطر تلف فوري. ترتفع تكاليف المخزون مع تحول الشركات إلى التخزين الطارئ.",
    },
    "infrastructure": {
        "why_affected": "Critical infrastructure — power grids, telecom networks, water desalination — underpins all other sectors. Infrastructure failure creates cascading dependencies: when power fails, banks cannot process transactions, hospitals lose equipment, and communications degrade.",
        "why_affected_ar": "البنية التحتية الحيوية — شبكات الكهرباء والاتصالات وتحلية المياه — تدعم جميع القطاعات الأخرى. فشل البنية التحتية يُحدث تبعيات متتالية: عندما تنقطع الكهرباء لا تستطيع البنوك معالجة المعاملات وتفقد المستشفيات المعدات وتتدهور الاتصالات.",
        "what_happens_next": "Backup generators provide 4-8 hours of coverage. After that, full operational degradation begins. Emergency coordination protocols activate across government agencies.",
        "what_happens_next_ar": "توفر المولدات الاحتياطية تغطية 4-8 ساعات. بعد ذلك يبدأ التدهور التشغيلي الكامل. تُفعَّل بروتوكولات التنسيق الطارئ عبر الجهات الحكومية.",
    },
    "government": {
        "why_affected": "Government and sovereign entities are affected through fiscal channel erosion — reduced tax/royalty revenue, sovereign credit spread widening, and increased emergency spending. Central banks must balance monetary stability with liquidity provision under stress.",
        "why_affected_ar": "تتأثر الكيانات الحكومية والسيادية من خلال تآكل القناة المالية — انخفاض الإيرادات الضريبية وحقوق الامتياز وتوسع فروق الائتمان السيادي وزيادة الإنفاق الطارئ. يجب على البنوك المركزية الموازنة بين الاستقرار النقدي وتوفير السيولة تحت الضغط.",
        "what_happens_next": "Budget reallocation decisions within 72 hours. Sovereign bond markets will reprice. Central bank may deploy emergency liquidity facilities. International credit rating agencies will place sovereign on review.",
        "what_happens_next_ar": "قرارات إعادة تخصيص الميزانية خلال 72 ساعة. ستعيد أسواق السندات السيادية التسعير. قد يُنشئ البنك المركزي تسهيلات سيولة طارئة. ستضع وكالات التصنيف الائتماني الدولية الكيان السيادي قيد المراجعة.",
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# Urgency classification
# ─────────────────────────────────────────────────────────────────────────────

def _urgency_label(risk_level: str, peak_day: int) -> tuple[str, str, str]:
    """Returns (urgency_en, urgency_ar, color_code)."""
    if risk_level in ("SEVERE", "HIGH") and peak_day <= 3:
        return ("CRITICAL — Immediate executive action required", "حرج — يتطلب إجراء تنفيذي فوري", "red")
    if risk_level in ("HIGH", "ELEVATED") and peak_day <= 7:
        return ("HIGH — Action needed within 24-48 hours", "مرتفع — يتطلب إجراء خلال 24-48 ساعة", "orange")
    if risk_level == "ELEVATED":
        return ("ELEVATED — Monitor closely, prepare contingency", "مرتفع — مراقبة دقيقة وإعداد خطط طوارئ", "yellow")
    if risk_level == "GUARDED":
        return ("GUARDED — Increased vigilance recommended", "حذر — يُوصى بزيادة اليقظة", "blue")
    return ("ROUTINE — Standard monitoring protocols", "روتيني — بروتوكولات المراقبة القياسية", "green")


# ─────────────────────────────────────────────────────────────────────────────
# Narrative Engine
# ─────────────────────────────────────────────────────────────────────────────

class NarrativeEngine:
    """Transforms SimulateResponse dict into executive narrative structure.

    Usage:
        engine = NarrativeEngine()
        narrative = engine.generate(simulation_result_dict)
    """

    def generate(self, result: dict) -> dict:
        """Generate the full narrative from a SimulateResponse dict.

        Returns a structured narrative dict with:
          executive_summary, causal_chain_story, sector_impact_stories,
          decision_rationale, governance_trust, metadata
        """
        scenario_id = result.get("scenario_id", "unknown")
        severity = result.get("severity", result.get("event_severity", 0.5))
        risk_level = result.get("risk_level", "NOMINAL")
        peak_day = result.get("peak_day", 1)
        confidence = result.get("confidence_score", 0.7)

        # Financial
        fi = result.get("financial_impact", {})
        total_loss = fi.get("total_loss_usd", 0.0)
        total_loss_fmt = fi.get("total_loss_formatted", format_loss_usd(total_loss))
        affected_entities = fi.get("affected_entities", 0)
        critical_entities = fi.get("critical_entities", 0)
        sector_losses = fi.get("sector_losses", [])

        # Determine top sector
        top_sector = "energy"
        if sector_losses:
            top_sector = max(sector_losses, key=lambda s: s.get("loss_usd", s.get("pct", 0))).get("sector", "energy")

        # Sector analysis
        sector_analysis = result.get("sector_analysis", [])
        affected_sectors = [s.get("sector", "") for s in sector_analysis if s.get("stress", 0) > 0.1]

        # Context
        ctx = _SCENARIO_CONTEXT.get(scenario_id, _DEFAULT_CONTEXT)
        urgency_en, urgency_ar, urgency_color = _urgency_label(risk_level, peak_day)

        # ── 1. Executive Summary ──────────────────────────────────────────
        executive_summary = self._build_executive_summary(
            scenario_id=scenario_id,
            severity=severity,
            risk_level=risk_level,
            total_loss_fmt=total_loss_fmt,
            total_loss_usd=total_loss,
            peak_day=peak_day,
            confidence=confidence,
            affected_entities=affected_entities,
            critical_entities=critical_entities,
            top_sector=top_sector,
            urgency_en=urgency_en,
            urgency_ar=urgency_ar,
            urgency_color=urgency_color,
            ctx=ctx,
        )

        # ── 2. Causal Chain Story ─────────────────────────────────────────
        causal_chain_story = self._build_causal_chain_story(
            result=result,
            ctx=ctx,
            top_sector=top_sector,
            affected_sectors=affected_sectors,
        )

        # ── 3. Sector Impact Stories ──────────────────────────────────────
        sector_stories = self._build_sector_stories(
            sector_analysis=sector_analysis,
            sector_losses=sector_losses,
            banking_stress=result.get("banking_stress", {}),
            insurance_stress=result.get("insurance_stress", {}),
            fintech_stress=result.get("fintech_stress", {}),
        )

        # ── 4. Decision Rationale ─────────────────────────────────────────
        decision_rationale = self._build_decision_rationale(
            decision_plan=result.get("decision_plan", {}),
            risk_level=risk_level,
            total_loss_usd=total_loss,
        )

        # ── 5. Governance & Trust ─────────────────────────────────────────
        governance = self._build_governance(
            result=result,
            confidence=confidence,
        )

        return {
            "narrative_available": True,
            "executive_summary": executive_summary,
            "causal_chain_story": causal_chain_story,
            "sector_stories": sector_stories,
            "decision_rationale": decision_rationale,
            "governance": governance,
            "metadata": {
                "scenario_id": scenario_id,
                "narrative_version": "1.0.0",
                "language": "bilingual",
                "urgency_level": urgency_en.split(" — ")[0],
                "urgency_color": urgency_color,
            },
        }

    # ─────────────────────────────────────────────────────────────────────
    # 1. Executive Summary
    # ─────────────────────────────────────────────────────────────────────

    def _build_executive_summary(
        self, *,
        scenario_id: str,
        severity: float,
        risk_level: str,
        total_loss_fmt: str,
        total_loss_usd: float,
        peak_day: int,
        confidence: float,
        affected_entities: int,
        critical_entities: int,
        top_sector: str,
        urgency_en: str,
        urgency_ar: str,
        urgency_color: str,
        ctx: dict,
    ) -> dict:
        scenario_name = scenario_id.replace("_", " ").title()
        confidence_pct = round(confidence * 100, 1)

        headline_en = (
            f"This scenario indicates a {risk_level.lower()}-risk disruption with an "
            f"estimated financial exposure of {total_loss_fmt} across GCC financial systems, "
            f"primarily driven by {top_sector} sector instability."
        )
        headline_ar = (
            f"يشير هذا السيناريو إلى اضطراب بمستوى خطورة {risk_level.lower()} مع "
            f"تعرض مالي مُقدَّر بـ {total_loss_fmt} عبر الأنظمة المالية الخليجية، "
            f"مدفوع أساساً بعدم استقرار قطاع {_SECTOR_NARRATIVES.get(top_sector, {}).get('why_affected_ar', top_sector)[:30]}."
        )

        return {
            "headline_en": headline_en,
            "headline_ar": headline_ar,
            "what_happened_en": ctx.get("signal", ""),
            "what_happened_ar": ctx.get("signal_ar", ""),
            "why_it_matters_en": ctx.get("strategic_context", ""),
            "why_it_matters_ar": ctx.get("strategic_context_ar", ""),
            "financial_exposure": {
                "total_loss_formatted": total_loss_fmt,
                "total_loss_usd": total_loss_usd,
                "affected_entities": affected_entities,
                "critical_entities": critical_entities,
            },
            "urgency": {
                "level_en": urgency_en,
                "level_ar": urgency_ar,
                "color": urgency_color,
                "peak_day": peak_day,
                "risk_level": risk_level,
            },
            "confidence": {
                "score": confidence,
                "percentage": confidence_pct,
                "interpretation_en": self._confidence_interpretation(confidence),
                "interpretation_ar": self._confidence_interpretation_ar(confidence),
            },
        }

    def _confidence_interpretation(self, c: float) -> str:
        if c >= 0.85:
            return "High confidence — model inputs well-calibrated, projections are reliable for decision-making."
        if c >= 0.70:
            return "Moderate confidence — projections are directionally reliable but should be cross-validated with subject matter experts."
        if c >= 0.50:
            return "Low-moderate confidence — significant uncertainty remains. Use as directional guidance only; seek additional data."
        return "Low confidence — insufficient data for reliable projections. Treat as worst-case scenario planning input."

    def _confidence_interpretation_ar(self, c: float) -> str:
        if c >= 0.85:
            return "ثقة عالية — مدخلات النموذج مُعايرة جيداً، التوقعات موثوقة لاتخاذ القرار."
        if c >= 0.70:
            return "ثقة متوسطة — التوقعات موثوقة اتجاهياً لكن يجب التحقق منها مع خبراء القطاع."
        if c >= 0.50:
            return "ثقة منخفضة-متوسطة — لا يزال هناك عدم يقين كبير. استخدم كتوجيه اتجاهي فقط؛ اطلب بيانات إضافية."
        return "ثقة منخفضة — بيانات غير كافية لتوقعات موثوقة. تعامل كمدخل تخطيط لأسوأ سيناريو."

    # ─────────────────────────────────────────────────────────────────────
    # 2. Causal Chain Story
    # ─────────────────────────────────────────────────────────────────────

    def _build_causal_chain_story(
        self, *,
        result: dict,
        ctx: dict,
        top_sector: str,
        affected_sectors: list[str],
    ) -> dict:
        explainability = result.get("explainability", {})
        causal_chain = explainability.get("causal_chain", [])

        # Build simplified propagation path
        chain_summary_parts = []
        seen_sectors = set()
        for step in causal_chain[:8]:
            sector = step.get("sector", "unknown")
            label = step.get("entity_label", sector)
            if sector not in seen_sectors:
                seen_sectors.add(sector)
                chain_summary_parts.append(label)

        propagation_path = " → ".join(chain_summary_parts) if chain_summary_parts else "Direct impact"

        # Build structured layers
        first_order = [s for s in causal_chain[:3] if s.get("hop", 0) <= 1]
        second_order = [s for s in causal_chain[3:8] if s.get("hop", 0) >= 2]
        tertiary = causal_chain[8:] if len(causal_chain) > 8 else []

        return {
            "root_cause_en": ctx.get("root_cause", ""),
            "root_cause_ar": ctx.get("root_cause_ar", ""),
            "propagation_path": propagation_path,
            "first_order_effects": [
                {
                    "entity": s.get("entity_label", ""),
                    "entity_ar": s.get("entity_label_ar", ""),
                    "mechanism_en": s.get("mechanism_en", ""),
                    "mechanism_ar": s.get("mechanism_ar", ""),
                    "impact_formatted": s.get("impact_usd_formatted", "$0"),
                    "confidence": s.get("confidence", 0),
                }
                for s in first_order
            ],
            "second_order_effects": [
                {
                    "entity": s.get("entity_label", ""),
                    "entity_ar": s.get("entity_label_ar", ""),
                    "mechanism_en": s.get("mechanism_en", ""),
                    "mechanism_ar": s.get("mechanism_ar", ""),
                    "impact_formatted": s.get("impact_usd_formatted", "$0"),
                    "confidence": s.get("confidence", 0),
                }
                for s in second_order
            ],
            "tertiary_effects_count": len(tertiary),
            "affected_sectors": affected_sectors,
            "total_chain_steps": len(causal_chain),
        }

    # ─────────────────────────────────────────────────────────────────────
    # 3. Sector Stories
    # ─────────────────────────────────────────────────────────────────────

    def _build_sector_stories(
        self, *,
        sector_analysis: list,
        sector_losses: list,
        banking_stress: dict,
        insurance_stress: dict,
        fintech_stress: dict,
    ) -> list[dict]:
        loss_by_sector = {s.get("sector", ""): s.get("loss_usd", s.get("pct", 0)) for s in sector_losses}
        stress_by_sector = {s.get("sector", ""): s for s in sector_analysis}

        stories = []
        for sector_key, templates in _SECTOR_NARRATIVES.items():
            stress_row = stress_by_sector.get(sector_key, {})
            stress_val = stress_row.get("stress", 0.0)
            exposure_val = stress_row.get("exposure", 0.0)
            classification = stress_row.get("classification", stress_row.get("risk_level", "NOMINAL"))
            loss_usd = loss_by_sector.get(sector_key, 0.0)

            if stress_val < 0.05 and loss_usd == 0:
                continue

            # Sector-specific metrics
            sector_metrics = {}
            if sector_key == "banking" and banking_stress:
                sector_metrics = {
                    "liquidity_stress": banking_stress.get("liquidity_stress", banking_stress.get("aggregate_stress", 0)),
                    "car_ratio": banking_stress.get("car_ratio", 0.12),
                    "lcr_ratio": banking_stress.get("lcr_ratio", 1.0),
                    "time_to_breach_hours": banking_stress.get("time_to_breach_hours", 9999),
                }
            elif sector_key == "insurance" and insurance_stress:
                sector_metrics = {
                    "combined_ratio": insurance_stress.get("combined_ratio", 1.0),
                    "claims_surge_multiplier": insurance_stress.get("claims_surge_multiplier", 1.0),
                    "reserve_adequacy_ratio": insurance_stress.get("reserve_adequacy_ratio", 1.0),
                    "reinsurance_trigger": insurance_stress.get("reinsurance_trigger", False),
                    "ifrs17_adjustment": insurance_stress.get("ifrs17_risk_adjustment_pct", 0),
                }
            elif sector_key == "fintech" and fintech_stress:
                sector_metrics = {
                    "payment_disruption_score": fintech_stress.get("payment_disruption_score", 0),
                    "settlement_delay_hours": fintech_stress.get("settlement_delay_hours", 0),
                    "api_availability_pct": fintech_stress.get("api_availability_pct", 100),
                    "cross_border_disruption": fintech_stress.get("cross_border_disruption", 0),
                }

            stories.append({
                "sector": sector_key,
                "classification": classification,
                "stress_score": round(stress_val, 4),
                "exposure": round(exposure_val, 4),
                "loss_usd": round(loss_usd, 2),
                "loss_formatted": format_loss_usd(loss_usd),
                "why_affected_en": templates["why_affected"],
                "why_affected_ar": templates["why_affected_ar"],
                "what_happens_next_en": templates["what_happens_next"],
                "what_happens_next_ar": templates["what_happens_next_ar"],
                "sector_metrics": sector_metrics,
            })

        stories.sort(key=lambda s: -s["stress_score"])
        return stories

    # ─────────────────────────────────────────────────────────────────────
    # 4. Decision Rationale
    # ─────────────────────────────────────────────────────────────────────

    def _build_decision_rationale(
        self, *,
        decision_plan: dict,
        risk_level: str,
        total_loss_usd: float,
    ) -> dict:
        actions = decision_plan.get("actions", [])
        immediate = decision_plan.get("immediate_actions", [])
        short_term = decision_plan.get("short_term_actions", [])
        five_q = decision_plan.get("five_questions", {})

        enriched_actions = []
        for act in actions[:10]:
            loss_avoided = act.get("loss_avoided_usd", 0)
            cost = act.get("cost_usd", 0)
            roi = round(loss_avoided / max(cost, 1), 1)

            # Why this decision exists
            why = (
                f"This action targets {act.get('sector', 'cross-sector')} sector exposure. "
                f"Implementing it avoids an estimated {act.get('loss_avoided_formatted', '$0')} in losses "
                f"at a cost of {act.get('cost_formatted', '$0')} (ROI: {roi}x)."
            )

            # What it mitigates
            mitigates = (
                f"Reduces {act.get('sector', 'systemic')} risk by addressing "
                f"{act.get('action', 'unspecified action')[:80]}."
            )

            # What happens if ignored
            if_ignored = (
                f"If not acted upon within {act.get('time_to_act_hours', 24)} hours, "
                f"exposure of {act.get('loss_avoided_formatted', '$0')} materializes. "
                f"Regulatory risk score: {act.get('regulatory_risk', 0):.0%}."
            )

            enriched_actions.append({
                "rank": act.get("rank", 0),
                "action_en": act.get("action", ""),
                "action_ar": act.get("action_ar", ""),
                "sector": act.get("sector", "cross-sector"),
                "priority_score": act.get("priority_score", 0),
                "time_to_act_hours": act.get("time_to_act_hours", 24),
                "loss_avoided_formatted": act.get("loss_avoided_formatted", "$0"),
                "cost_formatted": act.get("cost_formatted", "$0"),
                "roi_multiple": roi,
                "why_this_decision_en": why,
                "what_it_mitigates_en": mitigates,
                "if_ignored_en": if_ignored,
                "feasibility": act.get("feasibility", 0),
                "status": act.get("status", "PENDING_REVIEW"),
            })

        return {
            "total_actions": len(actions),
            "immediate_count": len(immediate),
            "short_term_count": len(short_term),
            "business_severity": decision_plan.get("business_severity", "LOW"),
            "time_to_first_failure_hours": decision_plan.get("time_to_first_failure_hours", 999),
            "five_questions": five_q,
            "actions": enriched_actions,
            "summary_en": (
                f"The decision engine recommends {len(actions)} actions across "
                f"{len(set(a.get('sector', '') for a in actions))} sectors. "
                f"{len(immediate)} require immediate attention (within 24 hours)."
            ),
            "summary_ar": (
                f"يوصي محرك القرار بـ {len(actions)} إجراء عبر "
                f"{len(set(a.get('sector', '') for a in actions))} قطاعات. "
                f"{len(immediate)} تتطلب اهتماماً فورياً (خلال 24 ساعة)."
            ),
        }

    # ─────────────────────────────────────────────────────────────────────
    # 5. Governance & Trust
    # ─────────────────────────────────────────────────────────────────────

    def _build_governance(self, *, result: dict, confidence: float) -> dict:
        explainability = result.get("explainability", {})
        uncertainty = explainability.get("uncertainty_bands", {})
        sensitivity = explainability.get("sensitivity", {})

        return {
            "audit_trail": {
                "run_id": result.get("run_id", ""),
                "model_version": result.get("model_version", "2.1.0"),
                "generated_at": result.get("generated_at", ""),
                "duration_ms": result.get("duration_ms", 0),
                "explanation_en": (
                    "Every simulation run generates a unique run_id and timestamps. "
                    "The SHA-256 audit hash ensures tamper-proof traceability. "
                    "All outputs are deterministic — identical inputs produce identical results."
                ),
                "explanation_ar": (
                    "تُنشئ كل عملية محاكاة معرف تشغيل فريد وطوابع زمنية. "
                    "يضمن تجزئة التدقيق SHA-256 إمكانية التتبع دون تلاعب. "
                    "جميع المخرجات حتمية — المدخلات المتطابقة تنتج نتائج متطابقة."
                ),
            },
            "model_certainty": {
                "confidence_score": confidence,
                "confidence_pct": round(confidence * 100, 1),
                "interpretation_en": self._confidence_interpretation(confidence),
                "interpretation_ar": self._confidence_interpretation_ar(confidence),
                "methodology": explainability.get("methodology", "deterministic_propagation"),
                "model_equation": explainability.get("model_equation", "R_i(t) = w1*G + w2*P + w3*N + w4*L + w5*T + w6*U"),
            },
            "uncertainty": {
                "lower_bound": uncertainty.get("lower_bound", 0),
                "upper_bound": uncertainty.get("upper_bound", 0),
                "band_width": uncertainty.get("band_width", 0),
                "interpretation_en": uncertainty.get("interpretation", ""),
                "explanation_en": (
                    "Uncertainty bands represent the range within which the true risk score "
                    "is expected to fall. Narrower bands indicate higher model confidence. "
                    "The band width is derived from: (1 - confidence) * 0.4."
                ),
                "explanation_ar": (
                    "تمثل نطاقات عدم اليقين المدى الذي يُتوقع أن تقع فيه درجة المخاطر الحقيقية. "
                    "النطاقات الأضيق تشير إلى ثقة أعلى في النموذج. "
                    "يُشتق عرض النطاق من: (1 - الثقة) × 0.4."
                ),
            },
            "sensitivity_summary": {
                "most_sensitive_parameter": sensitivity.get("most_sensitive_parameter", "severity"),
                "linearity_score": sensitivity.get("linearity_score", 0),
                "explanation_en": (
                    "Sensitivity analysis perturbs the severity input by ±10% and ±20% to measure "
                    "how output metrics change. A high linearity score means the model responds "
                    "proportionally; a low score indicates non-linear amplification of small changes."
                ),
                "explanation_ar": (
                    "يُعدّل تحليل الحساسية مدخل الشدة بنسبة ±10% و±20% لقياس "
                    "كيف تتغير مقاييس المخرجات. تعني درجة الخطية العالية أن النموذج يستجيب "
                    "بشكل متناسب؛ الدرجة المنخفضة تشير إلى تضخيم غير خطي للتغييرات الصغيرة."
                ),
            },
        }
