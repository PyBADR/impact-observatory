"""Seed events for GCC Decision Intelligence Platform."""

from datetime import datetime, timedelta
from app.schema import Event, EventType, SourceType, GeoPoint


def get_seed_events() -> list[Event]:
    """
    Return 50 realistic GCC conflict/security events covering:
    - Houthi drone/missile attacks (10 events)
    - Maritime incidents in Strait of Hormuz (8 events)
    - Iraq border tensions (5 events)
    - Iran naval provocations (7 events)
    - Red Sea shipping attacks (8 events)
    - Yemen conflict near GCC borders (7 events)
    - Internal security events (5 events)
    """
    events = []
    
    # Houthi drone/missile attacks on Saudi/UAE (10 events)
    houthi_attacks = [
        {
            "name": "Houthi drone attack on Riyadh Airport",
            "name_ar": "هجوم حوثي بطائرة مسيرة على مطار الرياض",
            "description": "Houthi unmanned aerial vehicle strike on King Khalid International Airport",
            "description_ar": "طائرة مسيرة حوثية استهدفت المنشآت الحيوية بمطار الملك خالد",
            "location": GeoPoint(latitude=24.9266, longitude=46.6989),  # Riyadh
            "start_time": datetime(2025, 11, 15, 3, 30),
            "severity": 0.85,
            "actors": ["houthi_movement"],
        },
        {
            "name": "Houthi ballistic missile strike on Jeddah Port",
            "name_ar": "صاروخ حوثي يستهدف ميناء جدة",
            "description": "Ballistic missile attack targeting Jeddah Islamic Port causing partial disruption",
            "description_ar": "صاروخ باليستي استهدف منشآت الميناء وأسفر عن أضرار محدودة",
            "location": GeoPoint(latitude=21.5433, longitude=39.1727),  # Jeddah Port
            "start_time": datetime(2025, 10, 22, 22, 15),
            "severity": 0.75,
            "actors": ["houthi_movement"],
        },
        {
            "name": "Houthi drone swarm on UAE oil facilities near Fujairah",
            "name_ar": "سرب طائرات حوثية يستهدف منشآت نفطية إماراتية",
            "description": "Multiple coordinated drone attacks on oil infrastructure near Fujairah port",
            "description_ar": "هجمات متعددة بطائرات مسيرة على المنشآت النفطية بالفجيرة",
            "location": GeoPoint(latitude=25.1166, longitude=56.3400),  # Fujairah
            "start_time": datetime(2025, 12, 3, 4, 45),
            "severity": 0.80,
            "actors": ["houthi_movement"],
        },
        {
            "name": "Houthi missile strike on Dammam refinery",
            "name_ar": "صاروخ حوثي يستهدف مصفاة الدمام",
            "description": "Cruise missile attack on King Fahd Industrial Port in Dammam area",
            "description_ar": "صاروخ باليستي استهدف منشآت ميناء الملك فهد الصناعي",
            "location": GeoPoint(latitude=26.1810, longitude=50.1992),  # Dammam
            "start_time": datetime(2025, 9, 28, 2, 20),
            "severity": 0.82,
            "actors": ["houthi_movement"],
        },
        {
            "name": "Houthi drone interception near Abu Dhabi",
            "name_ar": "اعتراض طائرة مسيرة حوثية بالقرب من أبوظبي",
            "description": "Multiple Houthi UAVs intercepted by UAE air defense near Abu Dhabi",
            "description_ar": "تم اعتراض عدد من الطائرات المسيرة الحوثية من قبل الدفاع الجوي الإماراتي",
            "location": GeoPoint(latitude=24.4539, longitude=54.3773),  # Abu Dhabi
            "start_time": datetime(2025, 11, 8, 5, 10),
            "severity": 0.72,
            "actors": ["houthi_movement"],
        },
        {
            "name": "Houthi attack on commercial vessel in Red Sea",
            "name_ar": "هجوم حوثي على سفينة تجارية في البحر الأحمر",
            "description": "Houthi forces fire on container ship in Red Sea shipping lane",
            "description_ar": "قوات حوثية تطلق النار على سفينة حاويات في ممر الملاحة بالبحر الأحمر",
            "location": GeoPoint(latitude=15.5527, longitude=42.8454),  # Red Sea
            "start_time": datetime(2025, 10, 5, 14, 30),
            "severity": 0.68,
            "actors": ["houthi_movement"],
        },
        {
            "name": "Houthi overnight drone barrage on Riyadh",
            "name_ar": "وابل من الطائرات المسيرة الحوثية على الرياض",
            "description": "Intensive multi-wave drone attack on Saudi capital overnight",
            "description_ar": "موجات متعددة من الطائرات المسيرة على العاصمة السعودية",
            "location": GeoPoint(latitude=24.7136, longitude=46.6753),  # Central Riyadh
            "start_time": datetime(2025, 12, 1, 23, 45),
            "severity": 0.88,
            "actors": ["houthi_movement"],
        },
        {
            "name": "Houthi boat strike attempt on Saudi naval vessel",
            "name_ar": "محاولة هجوم حوثي بزورق على سفينة حربية سعودية",
            "description": "Suicide boat attack on Saudi frigate in southern Red Sea",
            "description_ar": "محاولة هجوم بزورق فخاخ على فرقاطة سعودية",
            "location": GeoPoint(latitude=13.5116, longitude=43.1447),  # South Red Sea
            "start_time": datetime(2025, 11, 19, 16, 50),
            "severity": 0.78,
            "actors": ["houthi_movement"],
        },
        {
            "name": "Houthi capture of commercial fishing vessel",
            "name_ar": "الاستيلاء الحوثي على سفينة صيد تجارية",
            "description": "Houthi forces board and seize commercial fishing boat in Gulf of Aden",
            "description_ar": "استيلاء القوات الحوثية على سفينة صيد في خليج عدن",
            "location": GeoPoint(latitude=12.5891, longitude=44.2035),  # Gulf of Aden
            "start_time": datetime(2025, 11, 25, 10, 15),
            "severity": 0.55,
            "actors": ["houthi_movement"],
        },
        {
            "name": "Houthi drone battery on UAE military base",
            "name_ar": "هجوم طائرات مسيرة حوثية على قاعدة عسكرية إماراتية",
            "description": "Coordinated attack with drones and missiles on UAE military installation",
            "description_ar": "هجوم منسق من طائرات مسيرة وصواريخ على منشأة عسكرية إماراتية",
            "location": GeoPoint(latitude=24.2560, longitude=55.3667),  # Dubai area military
            "start_time": datetime(2025, 10, 12, 6, 30),
            "severity": 0.84,
            "actors": ["houthi_movement"],
        },
    ]
    
    # Maritime incidents in Strait of Hormuz (8 events)
    hormuz_incidents = [
        {
            "name": "Tanker collision near Strait of Hormuz entrance",
            "name_ar": "تصادم ناقلة بالقرب من مدخل مضيق هرمز",
            "description": "LNG carrier and bulk carrier near collision in congested shipping lane",
            "description_ar": "حادثة اقتراب خطيرة بين ناقلة غاز طبيعي وناقلة حبوب",
            "location": GeoPoint(latitude=26.1167, longitude=56.5167),  # Hormuz Strait
            "start_time": datetime(2025, 11, 10, 8, 45),
            "severity": 0.62,
            "actors": [],
        },
        {
            "name": "IRGC Navy intercepts commercial vessel for inspection",
            "name_ar": "البحرية الإيرانية توقف سفينة تجارية للتفتيش",
            "description": "Iranian Revolutionary Guard Corps Navy stops commercial vessel for inspection",
            "description_ar": "قوات الحرس الثوري البحرية توقف سفينة لإجراء تفتيش روتيني",
            "location": GeoPoint(latitude=26.0833, longitude=56.2500),  # Hormuz
            "start_time": datetime(2025, 10, 28, 11, 20),
            "severity": 0.48,
            "actors": ["iran_irgc_navy"],
        },
        {
            "name": "Oil spill incident from damaged tanker",
            "name_ar": "تسرب نفطي من ناقلة متضررة",
            "description": "Environmental incident from tanker hull damage in Hormuz waters",
            "description_ar": "حادث بيئي من تسرب نفط من هيكل ناقلة في مضيق هرمز",
            "location": GeoPoint(latitude=26.2333, longitude=56.4667),  # Central Hormuz
            "start_time": datetime(2025, 11, 1, 13, 0),
            "severity": 0.71,
            "actors": [],
        },
        {
            "name": "Iranian missile boat maneuvers near US carrier",
            "name_ar": "مناورات إيرانية بقارب صاروخي بالقرب من حاملة الطائرات الأمريكية",
            "description": "IRGC Navy fast-attack craft conduct close-quarters maneuvers",
            "description_ar": "زوارق إيرانية سريعة تقترب من حاملة الطائرات الأمريكية",
            "location": GeoPoint(latitude=26.5000, longitude=56.3000),  # Central Gulf
            "start_time": datetime(2025, 12, 5, 15, 30),
            "severity": 0.74,
            "actors": ["iran_irgc_navy"],
        },
        {
            "name": "Merchant vessel mechanical failure in Hormuz",
            "name_ar": "عطل ميكانيكي في سفينة تجارية بمضيق هرمز",
            "description": "Container ship engine failure causes temporary shipping lane obstruction",
            "description_ar": "عطل محرك في سفينة حاويات يسبب عرقلة الملاحة المؤقتة",
            "location": GeoPoint(latitude=26.1500, longitude=56.5000),  # Hormuz shipping lane
            "start_time": datetime(2025, 9, 15, 9, 10),
            "severity": 0.58,
            "actors": [],
        },
        {
            "name": "Reported submarine activity in Hormuz waters",
            "name_ar": "أنشطة غواصة مبلغ عنها في مياه مضيق هرمز",
            "description": "Unconfirmed reports of submarine detection in strategic waters",
            "description_ar": "تقارير غير مؤكدة عن كشف غواصة في المياه الاستراتيجية",
            "location": GeoPoint(latitude=26.0500, longitude=56.4500),  # Hormuz
            "start_time": datetime(2025, 11, 20, 3, 0),
            "severity": 0.52,
            "actors": [],
        },
        {
            "name": "UAE coast guard interdiction of smuggling vessel",
            "name_ar": "مداهمة الحرس الساحلي الإماراتي لسفينة تهريب",
            "description": "Coast guard intercepts suspected arms smuggling boat in territorial waters",
            "description_ar": "قوات الحرس الساحلي تعترض سفينة مريبة يشتبه بتهريب أسلحة",
            "location": GeoPoint(latitude=25.2667, longitude=55.3333),  # UAE territorial
            "start_time": datetime(2025, 10, 9, 18, 45),
            "severity": 0.45,
            "actors": [],
        },
        {
            "name": "Iran threatens to close Strait of Hormuz",
            "name_ar": "إيران تهدد بإغلاق مضيق هرمز",
            "description": "Iranian official warns of potential closure in response to sanctions",
            "description_ar": "مسؤول إيراني يحذر من احتمالية إغلاق المضيق ردا على العقوبات",
            "location": GeoPoint(latitude=26.1200, longitude=56.5200),  # Hormuz vicinity
            "start_time": datetime(2025, 11, 14, 10, 0),
            "severity": 0.68,
            "actors": ["iran"],
        },
    ]
    
    # Iraq border tensions (5 events)
    iraq_events = [
        {
            "name": "Cross-border shelling from Iraq-Saudi border",
            "name_ar": "قصف متبادل على الحدود السعودية العراقية",
            "description": "Artillery fire from Iraqi territory targeting Saudi border area",
            "description_ar": "قصف من الأراضي العراقية تجاه المنطقة الحدودية السعودية",
            "location": GeoPoint(latitude=29.7500, longitude=46.5000),  # Iraq-Saudi border
            "start_time": datetime(2025, 10, 18, 7, 30),
            "severity": 0.64,
            "actors": ["iraq_militias"],
        },
        {
            "name": "Kuwait-Iraq maritime boundary dispute",
            "name_ar": "نزاع على الحدود البحرية الكويتية العراقية",
            "description": "Iraqi naval presence reported in disputed waters near Kuwait",
            "description_ar": "وجود بحري عراقي مبلغ عنه في مياه متنازع عليها بالقرب من الكويت",
            "location": GeoPoint(latitude=29.2667, longitude=47.8333),  # Iraq-Kuwait waters
            "start_time": datetime(2025, 11, 22, 14, 15),
            "severity": 0.56,
            "actors": ["iraq"],
        },
        {
            "name": "Rocket attack on Iraqi military targets suspected",
            "name_ar": "هجوم صاروخي مشبوه على أهداف عسكرية عراقية",
            "description": "Unidentified rocket fire near Iraqi military bases suspected to originate from Saudi",
            "description_ar": "قصف صاروخي قرب قواعد عسكرية عراقية يشتبه بمصدره السعودي",
            "location": GeoPoint(latitude=30.9500, longitude=45.8500),  # Central Iraq
            "start_time": datetime(2025, 9, 25, 23, 20),
            "severity": 0.59,
            "actors": [],
        },
        {
            "name": "Iraqi militia drill near Saudi border",
            "name_ar": "تدريب لميليشيات عراقية بالقرب من الحدود السعودية",
            "description": "Large-scale military exercise by Iraqi militia groups near international border",
            "description_ar": "تمرين عسكري واسع النطاق لمليشيات عراقية بالقرب من الحدود الدولية",
            "location": GeoPoint(latitude=29.8333, longitude=46.3333),  # Iraq-Saudi region
            "start_time": datetime(2025, 11, 5, 6, 0),
            "severity": 0.51,
            "actors": ["iraq_militias"],
        },
        {
            "name": "Smuggling network dismantled on Iraq-Kuwait border",
            "name_ar": "تفكيك شبكة تهريب على الحدود العراقية الكويتية",
            "description": "Joint operation dismantle weapons smuggling operation",
            "description_ar": "عملية مشتركة لتفكيك شبكة تهريب أسلحة",
            "location": GeoPoint(latitude=29.4167, longitude=47.7500),  # Iraq-Kuwait border
            "start_time": datetime(2025, 10, 31, 9, 45),
            "severity": 0.42,
            "actors": [],
        },
    ]
    
    # Iran naval provocations in Gulf (7 events)
    iran_naval = [
        {
            "name": "Iranian surveillance drone shot down near Qatar",
            "name_ar": "إسقاط طائرة إيرانية بدون طيار بالقرب من قطر",
            "description": "Qatari air defense downs Iranian reconnaissance UAV in airspace",
            "description_ar": "دفاع جوي قطري يسقط طائرة إيرانية للاستطلاع",
            "location": GeoPoint(latitude=25.3500, longitude=51.1833),  # Qatar airspace
            "start_time": datetime(2025, 11, 9, 13, 50),
            "severity": 0.69,
            "actors": ["iran"],
        },
        {
            "name": "IRGC seizes foreign-flagged tanker",
            "name_ar": "الحرس الثوري الإيراني يستولي على ناقلة أجنبية",
            "description": "Iranian forces board and capture tanker in Persian Gulf waters",
            "description_ar": "قوات إيرانية تستولي على ناقلة نفط في مياه الخليج الفارسي",
            "location": GeoPoint(latitude=27.0000, longitude=52.5000),  # Central Persian Gulf
            "start_time": datetime(2025, 10, 6, 10, 30),
            "severity": 0.76,
            "actors": ["iran_irgc_navy"],
        },
        {
            "name": "Iranian frigate transit to Arabian Sea",
            "name_ar": "عبور فرقاطة إيرانية إلى بحر العرب",
            "description": "Iranian Navy frigate passes through Strait of Hormuz amid tensions",
            "description_ar": "فرقاطة بحرية إيرانية تعبر مضيق هرمز وسط التوترات",
            "location": GeoPoint(latitude=26.1667, longitude=56.3333),  # Hormuz Strait
            "start_time": datetime(2025, 11, 17, 8, 0),
            "severity": 0.54,
            "actors": ["iran"],
        },
        {
            "name": "Iranian missile test in Persian Gulf",
            "name_ar": "اختبار إيراني صاروخي في الخليج الفارسي",
            "description": "Iran conducts ballistic missile test in disputed territorial waters",
            "description_ar": "إيران تجري اختبار صاروخ باليستي في مياه متنازع عليها",
            "location": GeoPoint(latitude=26.8333, longitude=52.0000),  # Persian Gulf
            "start_time": datetime(2025, 12, 2, 11, 0),
            "severity": 0.77,
            "actors": ["iran"],
        },
        {
            "name": "Bahrain coast guard intercepts Iranian boat",
            "name_ar": "الحرس الساحلي البحريني يعترض قارب إيراني",
            "description": "Bahraini forces intercept Iranian vessel in disputed waters",
            "description_ar": "قوات بحرينية تعترض سفينة إيرانية في مياه متنازع عليها",
            "location": GeoPoint(latitude=26.1833, longitude=50.3500),  # Bahrain waters
            "start_time": datetime(2025, 11, 3, 15, 20),
            "severity": 0.50,
            "actors": ["iran"],
        },
        {
            "name": "Iranian underwater mine detection exercise",
            "name_ar": "تمرين إيراني لكشف الألغام تحت الماء",
            "description": "Iran announces underwater mine detection exercises in Persian Gulf",
            "description_ar": "إيران تعلن عن تمارين كشف الألغام البحرية في الخليج الفارسي",
            "location": GeoPoint(latitude=27.5000, longitude=51.5000),  # Iranian waters
            "start_time": datetime(2025, 10, 19, 6, 0),
            "severity": 0.47,
            "actors": ["iran"],
        },
        {
            "name": "Iranian merchant vessel delayed at UAE port inspection",
            "name_ar": "تأخير سفينة تجارية إيرانية في ميناء إماراتي",
            "description": "Extended inspection of Iranian flagged vessel over compliance concerns",
            "description_ar": "فحص مطول لسفينة إيرانية بسبب مخاوف من الامتثال",
            "location": GeoPoint(latitude=25.2708, longitude=55.2973),  # Port Rashid Dubai
            "start_time": datetime(2025, 11, 23, 7, 45),
            "severity": 0.38,
            "actors": [],
        },
    ]
    
    # Red Sea shipping attacks (8 events)
    red_sea_attacks = [
        {
            "name": "Container ship attacked in Red Sea shipping lane",
            "name_ar": "هجوم على سفينة حاويات في ممر الملاحة بالبحر الأحمر",
            "description": "Armed group fires on international container vessel",
            "description_ar": "مجموعة مسلحة تطلق النار على سفينة حاويات دولية",
            "location": GeoPoint(latitude=14.8, longitude=42.4),  # Red Sea lane
            "start_time": datetime(2025, 11, 11, 16, 30),
            "severity": 0.73,
            "actors": ["houthi_movement"],
        },
        {
            "name": "Bulk carrier hijacked in Red Sea",
            "name_ar": "اختطاف سفينة ناقلة حبوب في البحر الأحمر",
            "description": "Unidentified armed forces board and seize bulk carrier vessel",
            "description_ar": "قوات مسلحة تجهيل الهوية تستولي على سفينة حبوب",
            "location": GeoPoint(latitude=13.5, longitude=43.0),  # South Red Sea
            "start_time": datetime(2025, 10, 20, 12, 0),
            "severity": 0.70,
            "actors": ["houthi_movement"],
        },
        {
            "name": "Distress call from chemical tanker in Red Sea",
            "name_ar": "نداء استغاثة من ناقلة كيماويات في البحر الأحمر",
            "description": "Chemical tanker sends distress signal after attack in Red Sea",
            "description_ar": "ناقلة كيماويات ترسل نداء استغاثة بعد هجوم في البحر الأحمر",
            "location": GeoPoint(latitude=15.2, longitude=42.7),  # Red Sea
            "start_time": datetime(2025, 12, 4, 18, 15),
            "severity": 0.80,
            "actors": ["houthi_movement"],
        },
        {
            "name": "General cargo ship reports near miss with missiles",
            "name_ar": "سفينة شحن عام تبلغ عن شبه انفجار من صواريخ",
            "description": "General cargo vessel reports missile impacts near shipping lane",
            "description_ar": "سفينة شحن تبلغ عن انفجارات صاروخية بالقرب من ممر الملاحة",
            "location": GeoPoint(latitude=14.3, longitude=42.9),  # Red Sea
            "start_time": datetime(2025, 11, 27, 11, 45),
            "severity": 0.75,
            "actors": ["houthi_movement"],
        },
        {
            "name": "Egyptian Navy engages suspected pirate vessel",
            "name_ar": "البحرية المصرية تشارك سفينة مريبة",
            "description": "Egyptian Navy intercepts vessel suspected of piracy activities",
            "description_ar": "البحرية المصرية تعترض سفينة مريبة يشتبه بنشاطات قرصنة",
            "location": GeoPoint(latitude=18.0, longitude=39.0),  # Northern Red Sea
            "start_time": datetime(2025, 9, 8, 9, 20),
            "severity": 0.44,
            "actors": [],
        },
        {
            "name": "LNG carrier attacks reported near Bab el-Mandeb",
            "name_ar": "هجمات على ناقلة غاز طبيعي بالقرب من باب المندب",
            "description": "LNG tanker reports gunfire while transiting Bab el-Mandeb passage",
            "description_ar": "ناقلة غاز تبلغ عن إطلاق نار أثناء عبورها باب المندب",
            "location": GeoPoint(latitude=12.6, longitude=43.2),  # Bab el-Mandeb
            "start_time": datetime(2025, 11, 6, 14, 0),
            "severity": 0.72,
            "actors": ["houthi_movement"],
        },
        {
            "name": "Djibouti Coast Guard rescue of attacked vessel crew",
            "name_ar": "إنقاذ بحري جيبوتي لطاقم سفينة مهاجمة",
            "description": "Djibouti Coast Guard rescues crew from attacked merchant vessel",
            "description_ar": "الحرس الساحلي الجيبوتي ينقذ طاقم سفينة تجارية تعرضت للهجوم",
            "location": GeoPoint(latitude=11.6, longitude=43.3),  # Djibouti waters
            "start_time": datetime(2025, 10, 14, 6, 30),
            "severity": 0.60,
            "actors": [],
        },
        {
            "name": "Fishing vessel reported stolen in Red Sea",
            "name_ar": "سفينة صيد مسروقة تبلغ عنها في البحر الأحمر",
            "description": "Commercial fishing vessel disappears off Eritrea coast",
            "description_ar": "سفينة صيد تجارية تختفي قبالة السواحل الإريترية",
            "location": GeoPoint(latitude=15.8, longitude=41.0),  # Eritrea coast
            "start_time": datetime(2025, 11, 13, 4, 0),
            "severity": 0.52,
            "actors": [],
        },
    ]
    
    # Yemen conflict events near GCC borders (7 events)
    yemen_events = [
        {
            "name": "Houthi mortar barrage on Saudi southern province",
            "name_ar": "وابل هاون حوثي على المحافظة السعودية الجنوبية",
            "description": "Houthi forces fire mortar rounds into Saudi Najran province",
            "description_ar": "قوات حوثية تطلق قذائف هاون في محافظة نجران السعودية",
            "location": GeoPoint(latitude=17.4919, longitude=44.1260),  # Najran
            "start_time": datetime(2025, 10, 24, 5, 30),
            "severity": 0.65,
            "actors": ["houthi_movement"],
        },
        {
            "name": "Yemen government forces artillery strikes",
            "name_ar": "قصف مدفعي من قوات الحكومة اليمنية",
            "description": "Saudi-backed Yemeni forces conduct artillery operations on Houthi positions",
            "description_ar": "قوات حكومية يمنية تدعمها السعودية تشن عمليات مدفعية",
            "location": GeoPoint(latitude=15.5527, longitude=48.5164),  # Eastern Yemen
            "start_time": datetime(2025, 11, 12, 7, 45),
            "severity": 0.61,
            "actors": ["yemen_government", "saudi_arabia"],
        },
        {
            "name": "Cross-fire incident affecting Saudi border town",
            "name_ar": "حادثة تبادل نيران تؤثر على مدينة سعودية حدودية",
            "description": "Stray fire from Yemen reaches Saudi settlement causing evacuations",
            "description_ar": "قصف عابر من اليمن يصل إلى مستوطنة سعودية",
            "location": GeoPoint(latitude=16.8951, longitude=42.5521),  # Asir border
            "start_time": datetime(2025, 10, 30, 10, 15),
            "severity": 0.59,
            "actors": ["houthi_movement"],
        },
        {
            "name": "Drone incursion from Yemen into Saudi territory",
            "name_ar": "اخترقت طائرة بدون طيار من اليمن الأراضي السعودية",
            "description": "Unidentified drone crosses from Yemen into Saudi airspace over Asir",
            "description_ar": "طائرة مسيرة مجهولة تخترق المجال الجوي السعودي",
            "location": GeoPoint(latitude=17.6, longitude=42.8),  # Asir region
            "start_time": datetime(2025, 11, 21, 2, 30),
            "severity": 0.57,
            "actors": [],
        },
        {
            "name": "Humanitarian corridor opens through Yemen territory",
            "name_ar": "فتح ممر إنساني عبر الأراضي اليمنية",
            "description": "Temporary ceasefire allows humanitarian aid passage through Yemeni conflict zone",
            "description_ar": "هدنة مؤقتة تسمح بمرور المساعدات الإنسانية",
            "location": GeoPoint(latitude=15.4729, longitude=48.5194),  # Central Yemen
            "start_time": datetime(2025, 9, 22, 6, 0),
            "severity": 0.30,
            "actors": ["yemen_government", "houthi_movement"],
        },
        {
            "name": "UAE reports airspace incursion from Yemen",
            "name_ar": "تقرير إماراتي عن اخترقا الفضاء الجوي من اليمن",
            "description": "Unidentified aircraft briefly enters UAE airspace from Yemen",
            "description_ar": "طائرة مجهولة تدخل المجال الجوي الإماراتي",
            "location": GeoPoint(latitude=23.2, longitude=53.8),  # UAE airspace
            "start_time": datetime(2025, 11, 30, 3, 20),
            "severity": 0.51,
            "actors": [],
        },
        {
            "name": "Saudi-Yemen border checkpoint skirmish",
            "name_ar": "اشتباك على نقطة تفتيش الحدود السعودية اليمنية",
            "description": "Armed clash at Yemeni-Saudi border crossing",
            "description_ar": "اشتباك مسلح على معبر حدودي سعودي يمني",
            "location": GeoPoint(latitude=17.4667, longitude=42.7667),  # Najran-Yemen border
            "start_time": datetime(2025, 10, 11, 14, 50),
            "severity": 0.66,
            "actors": ["yemen_government"],
        },
    ]
    
    # Internal GCC security events (5 events)
    internal_security = [
        {
            "name": "Counter-terrorism raid in Saudi Arabia",
            "name_ar": "عملية مكافحة إرهاب في المملكة العربية السعودية",
            "description": "Security forces conduct raid on suspected militant cell in Riyadh suburbs",
            "description_ar": "قوات الأمن تشن غارة على خلية إرهابية مشبوهة",
            "location": GeoPoint(latitude=24.7000, longitude=46.5500),  # Riyadh suburbs
            "start_time": datetime(2025, 11, 26, 4, 0),
            "severity": 0.56,
            "actors": [],
        },
        {
            "name": "UAE arrests alleged espionage ring",
            "name_ar": "اعتقالات إماراتية لشبكة تجسس مشبوهة",
            "description": "UAE security services arrest alleged foreign intelligence operatives",
            "description_ar": "خدمات الأمن الإماراتية تعتقل جواسيس أجانب مشبوهين",
            "location": GeoPoint(latitude=25.2048, longitude=55.2708),  # Dubai
            "start_time": datetime(2025, 10, 2, 9, 30),
            "severity": 0.63,
            "actors": [],
        },
        {
            "name": "Kuwait announces cyber security incident",
            "name_ar": "الكويت تعلن عن حادث أمن سيبراني",
            "description": "Kuwait government reports successful defense against cyber attack",
            "description_ar": "حكومة الكويت تعلن عن دفع هجوم سيبراني",
            "location": GeoPoint(latitude=29.3759, longitude=47.9774),  # Kuwait City
            "start_time": datetime(2025, 11, 8, 11, 0),
            "severity": 0.49,
            "actors": [],
        },
        {
            "name": "Bahrain security drill in capital",
            "name_ar": "تدريب أمني بحريني في العاصمة",
            "description": "Large-scale security exercise in Bahrain involving multiple agencies",
            "description_ar": "تمرين أمني واسع النطاق يشمل عدة أجهزة",
            "location": GeoPoint(latitude=26.1667, longitude=50.5500),  # Manama
            "start_time": datetime(2025, 10, 16, 6, 0),
            "severity": 0.35,
            "actors": [],
        },
        {
            "name": "Oman detains suspected smuggler at port",
            "name_ar": "عمان توقيف مهرب مشبوه في الميناء",
            "description": "Omani customs intercept suspected drug smugglers at Muscat port",
            "description_ar": "الجمارك العمانية تعترض مهربي مخدرات مشبوهين",
            "location": GeoPoint(latitude=23.6100, longitude=58.5400),  # Muscat Port
            "start_time": datetime(2025, 11, 2, 13, 20),
            "severity": 0.46,
            "actors": [],
        },
    ]
    
    all_events = houthi_attacks + hormuz_incidents + iraq_events + iran_naval + red_sea_attacks + yemen_events + internal_security
    
    for idx, event_data in enumerate(all_events):
        event = Event(
            name=event_data["name"],
            description=event_data["description"],
            description_ar=event_data.get("description_ar"),
            event_type=EventType.SECURITY,
            severity=event_data["severity"],
            location=event_data["location"],
            start_time=event_data["start_time"],
            actors=event_data.get("actors", []),
            source_type=SourceType.NEWS_FEED,
            confidence=0.65 + (idx % 3) * 0.15,
            tags=[
                "gcc-conflict",
                "maritime" if "maritime" in event_data["description"].lower() or "vessel" in event_data["description"].lower() or "port" in event_data["description"].lower() else "land",
                "houthi" if "houthi" in event_data["name"].lower() else "regional",
            ],
        )
        events.append(event)
    
    return events


if __name__ == "__main__":
    seed_events = get_seed_events()
    print(f"Loaded {len(seed_events)} seed events")
    for event in seed_events[:3]:
        print(f"  - {event.name} ({event.event_type}) - Severity: {event.severity}")
