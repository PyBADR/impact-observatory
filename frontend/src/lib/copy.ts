/**
 * Impact Observatory | مرصد الأثر — Product Copy
 *
 * All user-facing copy constants.
 * Business language only — no engineering vocabulary.
 * Arabic translations included where they appear in UI.
 */

export const brand = {
  name:          'Impact Observatory',
  nameAr:        'مرصد الأثر',
  tagline:       'From Macro Signals to Economic Decisions',
  taglineAr:     'من الإشارات الكلية إلى القرارات الاقتصادية',
  description:   'Understand how shocks move across GCC economies — and who must act.',
  descriptionAr: 'افهم كيف تنتقل الصدمات عبر اقتصادات مجلس التعاون الخليجي — ومن يجب أن يتصرف.',
} as const;

export const navigation = {
  overview:   'Overview',
  scenarios:  'Scenarios',
  decisions:  'Decisions',
  evaluation: 'Evaluation',
} as const;

export const landing = {
  heroTitle: 'From Macro Signals\nto Economic Decisions',
  heroSubtitle:
    'Understand how shocks move across GCC economies — and who must act.',

  steps: [
    {
      number: '01',
      title: 'Signal Detection',
      description:
        'Monitor macro shocks — energy disruptions, liquidity stress, trade corridor failures — as they emerge across the GCC.',
    },
    {
      number: '02',
      title: 'Impact Transmission',
      description:
        'Trace how economic pressure moves through sectors, institutions, and sovereign exposures with full causal transparency.',
    },
    {
      number: '03',
      title: 'Decision & Evaluation',
      description:
        'Surface the right decision for the right institution — then measure whether it worked.',
    },
  ],

  scenariosHeading:    'Active Scenarios',
  scenariosSubheading: 'Each scenario represents a macro shock with measurable economic consequences across GCC markets.',

  sectorsHeading: 'Sector Coverage',
  sectors: [
    { name: 'Banking',     description: 'Liquidity, credit exposure, cross-border flows' },
    { name: 'Insurance',   description: 'Underwriting pressure, catastrophe reserves, reinsurance' },
    { name: 'Fintech',     description: 'Payment disruption, regulatory risk, funding stress' },
    { name: 'Real Estate', description: 'Valuation pressure, construction pipeline, demand shifts' },
    { name: 'Government',  description: 'Fiscal burden, sovereign exposure, policy response' },
  ],

  whyHeading: 'Why This Matters',
  whyBody:
    'GCC economies are deeply interconnected. A disruption in one corridor ripples through energy, trade, banking, and sovereign stability. Impact Observatory maps these transmissions so decision-makers can act before exposure becomes loss.',
} as const;

export const scenario = {
  signalLabel:                'Signal',
  transmissionLabel:          'Transmission Path',
  economicImpactLabel:        'Economic Impact',
  sectorExposureLabel:        'Sector Exposure',
  institutionalPressureLabel: 'Institutional Pressure',
  decisionLabel:              'Recommended Decision',
  expectedOutcomeLabel:       'Expected Outcome',
} as const;

export const decision = {
  whyLabel:        'Why This Decision',
  ownerLabel:      'Decision Owner',
  deadlineLabel:   'Response Deadline',
  escalationLabel: 'Escalation Path',
  rationaleLabel:  'Rationale',
  mitigationLabel: 'Expected Mitigation',
  auditLabel:      'Audit Trail',
} as const;

export const evaluation = {
  heading:            'Decision Evaluation',
  subheading:         'Compare expected outcomes against actual results. Review analyst feedback and replay summaries.',
  expectedLabel:      'Expected Outcome',
  actualLabel:        'Actual Outcome',
  correctnessLabel:   'Correctness Score',
  feedbackLabel:      'Analyst Feedback',
  replayLabel:        'Replay Summary',
  rulePerformanceLabel: 'Rule Performance',
} as const;
