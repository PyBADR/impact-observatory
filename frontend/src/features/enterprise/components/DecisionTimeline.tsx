"use client";

import React, { useState, useCallback, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown, ChevronUp, ChevronLeft, ChevronRight } from "lucide-react";
import type { DecisionTimelineEvent, TimelineEventType } from "@/types/enterprise";
import { theme } from "@/theme/tokens";

interface DecisionTimelineProps {
  events: DecisionTimelineEvent[];
  language: "en" | "ar";
  onEventSelect?: (event: DecisionTimelineEvent) => void;
}

const eventTypeLabels: Record<TimelineEventType, { en: string; ar: string }> = {
  signal_ingested: { en: "Signal Ingested", ar: "تم استقبال الإشارة" },
  scenario_triggered: { en: "Scenario Triggered", ar: "تم تفعيل السيناريو" },
  simulation_started: { en: "Simulation Started", ar: "بدء المحاكاة" },
  simulation_completed: { en: "Simulation Completed", ar: "انتهت المحاكاة" },
  policy_check: { en: "Policy Check", ar: "فحص السياسة" },
  risk_scored: { en: "Risk Scored", ar: "تم تقييم المخاطر" },
  decision_proposed: { en: "Decision Proposed", ar: "تم اقتراح القرار" },
  decision_reviewed: { en: "Decision Reviewed", ar: "تم مراجعة القرار" },
  decision_approved: { en: "Decision Approved", ar: "تم الموافقة على القرار" },
  decision_rejected: { en: "Decision Rejected", ar: "تم رفض القرار" },
  decision_executed: { en: "Decision Executed", ar: "تم تنفيذ القرار" },
  outcome_observed: { en: "Outcome Observed", ar: "تم ملاحظة النتيجة" },
  override_applied: { en: "Override Applied", ar: "تم تطبيق التجاوز" },
};

const getSeverityColor = (
  severity?: string
): string => {
  switch (severity) {
    case "CRITICAL":
      return theme.classification.critical;
    case "ELEVATED":
      return theme.classification.elevated;
    case "MODERATE":
      return theme.classification.moderate;
    case "LOW":
      return theme.classification.low;
    case "NOMINAL":
      return theme.classification.nominal;
    default:
      return theme.palette.secondary;
  }
};

interface ExpandedEvent {
  id: string;
}

export const DecisionTimeline: React.FC<DecisionTimelineProps> = ({
  events,
  language,
  onEventSelect,
}) => {
  const [expandedEvents, setExpandedEvents] = useState<ExpandedEvent[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [filterType, setFilterType] = useState<TimelineEventType | "all">("all");

  const filteredEvents = useMemo(() => {
    if (filterType === "all") return events;
    return events.filter((e) => e.type === filterType);
  }, [events, filterType]);

  const sortedEvents = useMemo(() => {
    return [...filteredEvents].sort(
      (a, b) =>
        new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
    );
  }, [filteredEvents]);

  const isExpanded = useCallback(
    (eventId: string) => expandedEvents.some((e) => e.id === eventId),
    [expandedEvents]
  );

  const toggleExpand = useCallback((eventId: string) => {
    setExpandedEvents((prev) => {
      const exists = prev.some((e) => e.id === eventId);
      if (exists) {
        return prev.filter((e) => e.id !== eventId);
      } else {
        return [...prev, { id: eventId }];
      }
    });
  }, []);

  const handlePrevious = useCallback(() => {
    setCurrentIndex((prev) => Math.max(0, prev - 1));
  }, []);

  const handleNext = useCallback(() => {
    setCurrentIndex((prev) =>
      Math.min(sortedEvents.length - 1, prev + 1)
    );
  }, [sortedEvents.length]);

  const eventTypeOptions = useMemo(() => {
    const types = new Set(events.map((e) => e.type));
    return Array.from(types).sort();
  }, [events]);

  if (sortedEvents.length === 0) {
    return (
      <div
        style={{
          padding: theme.spacing.xl,
          textAlign: "center",
          backgroundColor: theme.palette.surface,
          borderRadius: theme.borderRadius.lg,
          border: `1px solid ${theme.palette.border}`,
          color: theme.palette.secondary,
          fontFamily: theme.typography.fontFamily,
        }}
      >
        No events available
      </div>
    );
  }

  const currentEvent = sortedEvents[currentIndex];
  const eventTypeLabel = eventTypeLabels[currentEvent.type];

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: theme.spacing.xl,
        backgroundColor: theme.palette.background,
        padding: theme.spacing.xl,
        borderRadius: theme.borderRadius.lg,
        fontFamily: language === "ar" ? theme.typography.fontFamilyAr : theme.typography.fontFamily,
      }}
    >
      {/* Filter Controls */}
      <div
        style={{
          display: "flex",
          gap: theme.spacing.md,
          flexWrap: "wrap",
          alignItems: "center",
        }}
      >
        <label
          style={{
            fontSize: "0.875rem",
            fontWeight: 500,
            color: theme.palette.secondary,
          }}
        >
          Filter by type:
        </label>
        <select
          value={filterType}
          onChange={(e) => {
            setFilterType(e.target.value as TimelineEventType | "all");
            setCurrentIndex(0);
          }}
          style={{
            padding: `${theme.spacing.sm} ${theme.spacing.md}`,
            borderRadius: theme.borderRadius.md,
            border: `1px solid ${theme.palette.border}`,
            backgroundColor: theme.palette.surface,
            fontFamily: "inherit",
            fontSize: "0.875rem",
            color: theme.palette.primary,
            cursor: "pointer",
          }}
        >
          <option value="all">All Events</option>
          {eventTypeOptions.map((type) => (
            <option key={type} value={type}>
              {eventTypeLabels[type][language]}
            </option>
          ))}
        </select>
      </div>

      {/* Timeline Container */}
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          gap: theme.spacing.lg,
        }}
      >
        {/* Current Event Focus */}
        <div
          style={{
            backgroundColor: theme.palette.surface,
            borderRadius: theme.borderRadius.lg,
            padding: theme.spacing.xl,
            border: `2px solid ${getSeverityColor(currentEvent.severity)}`,
            boxShadow: theme.shadow.md,
          }}
        >
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr",
              gap: theme.spacing.lg,
            }}
          >
            {/* Left Column */}
            <div>
              <div
                style={{
                  fontSize: "0.75rem",
                  fontWeight: 500,
                  color: theme.palette.secondary,
                  textTransform: "uppercase",
                  letterSpacing: "0.04em",
                  marginBottom: theme.spacing.sm,
                }}
              >
                Event {currentIndex + 1} of {sortedEvents.length}
              </div>
              <div
                style={{
                  fontSize: "1.5rem",
                  fontWeight: 600,
                  color: theme.palette.primary,
                  marginBottom: theme.spacing.md,
                }}
              >
                {eventTypeLabel[language]}
              </div>
              <div
                style={{
                  fontSize: "0.875rem",
                  color: theme.palette.secondary,
                  marginBottom: theme.spacing.md,
                }}
              >
                {new Date(currentEvent.timestamp).toLocaleString(
                  language === "ar" ? "ar-SA" : "en-US"
                )}
              </div>
              {currentEvent.actor && (
                <div
                  style={{
                    fontSize: "0.875rem",
                    color: theme.palette.secondary,
                  }}
                >
                  <strong>Actor:</strong> {currentEvent.actor}
                </div>
              )}
            </div>

            {/* Right Column */}
            <div>
              {currentEvent.severity && (
                <div
                  style={{
                    display: "inline-block",
                    padding: `${theme.spacing.sm} ${theme.spacing.md}`,
                    backgroundColor: getSeverityColor(currentEvent.severity),
                    color: theme.palette.surface,
                    borderRadius: theme.borderRadius.md,
                    fontSize: "0.75rem",
                    fontWeight: 600,
                    textTransform: "uppercase",
                    letterSpacing: "0.04em",
                    marginBottom: theme.spacing.md,
                  }}
                >
                  {currentEvent.severity}
                </div>
              )}
              <div
                style={{
                  fontSize: "0.875rem",
                  lineHeight: 1.6,
                  color: theme.palette.primary,
                  marginTop: theme.spacing.md,
                }}
              >
                {currentEvent.description}
              </div>
            </div>
          </div>

          {/* Metadata Section */}
          {currentEvent.metadata && Object.keys(currentEvent.metadata).length > 0 && (
            <div
              style={{
                marginTop: theme.spacing.lg,
                paddingTop: theme.spacing.lg,
                borderTop: `1px solid ${theme.palette.border}`,
              }}
            >
              <div
                style={{
                  fontSize: "0.75rem",
                  fontWeight: 600,
                  color: theme.palette.secondary,
                  textTransform: "uppercase",
                  letterSpacing: "0.04em",
                  marginBottom: theme.spacing.md,
                }}
              >
                Additional Details
              </div>
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
                  gap: theme.spacing.md,
                }}
              >
                {Object.entries(currentEvent.metadata).map(([key, value]) => (
                  <div key={key}>
                    <div
                      style={{
                        fontSize: "0.75rem",
                        color: theme.palette.secondary,
                        marginBottom: theme.spacing.xs,
                      }}
                    >
                      {key}
                    </div>
                    <div
                      style={{
                        fontSize: "0.875rem",
                        color: theme.palette.primary,
                        fontWeight: 500,
                      }}
                    >
                      {String(value)}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Navigation Controls */}
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            gap: theme.spacing.md,
          }}
        >
          <button
            onClick={handlePrevious}
            disabled={currentIndex === 0}
            style={{
              display: "flex",
              alignItems: "center",
              gap: theme.spacing.sm,
              padding: `${theme.spacing.sm} ${theme.spacing.md}`,
              backgroundColor:
                currentIndex === 0
                  ? theme.palette.border
                  : theme.palette.accent,
              color: theme.palette.surface,
              border: "none",
              borderRadius: theme.borderRadius.md,
              cursor: currentIndex === 0 ? "not-allowed" : "pointer",
              fontSize: "0.875rem",
              fontWeight: 500,
              opacity: currentIndex === 0 ? 0.5 : 1,
              fontFamily: "inherit",
            }}
          >
            <ChevronLeft size={16} />
            Previous
          </button>

          <div
            style={{
              fontSize: "0.875rem",
              color: theme.palette.secondary,
              fontWeight: 500,
            }}
          >
            {currentIndex + 1} / {sortedEvents.length}
          </div>

          <button
            onClick={handleNext}
            disabled={currentIndex === sortedEvents.length - 1}
            style={{
              display: "flex",
              alignItems: "center",
              gap: theme.spacing.sm,
              padding: `${theme.spacing.sm} ${theme.spacing.md}`,
              backgroundColor:
                currentIndex === sortedEvents.length - 1
                  ? theme.palette.border
                  : theme.palette.accent,
              color: theme.palette.surface,
              border: "none",
              borderRadius: theme.borderRadius.md,
              cursor:
                currentIndex === sortedEvents.length - 1
                  ? "not-allowed"
                  : "pointer",
              fontSize: "0.875rem",
              fontWeight: 500,
              opacity:
                currentIndex === sortedEvents.length - 1 ? 0.5 : 1,
              fontFamily: "inherit",
            }}
          >
            Next
            <ChevronRight size={16} />
          </button>
        </div>

        {/* Timeline List with Expandable Details */}
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            gap: theme.spacing.sm,
            maxHeight: "400px",
            overflowY: "auto",
            paddingRight: theme.spacing.md,
          }}
        >
          <AnimatePresence mode="popLayout">
            {sortedEvents.map((event, index) => (
              <motion.div
                key={event.id}
                layout
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.2 }}
              >
                <div
                  onClick={() => {
                    setCurrentIndex(index);
                    onEventSelect?.(event);
                  }}
                  style={{
                    padding: theme.spacing.md,
                    backgroundColor:
                      index === currentIndex
                        ? theme.palette.accent
                        : theme.palette.surface,
                    border: `1px solid ${
                      index === currentIndex
                        ? theme.palette.accent
                        : theme.palette.border
                    }`,
                    borderRadius: theme.borderRadius.md,
                    cursor: "pointer",
                    transition: "all 0.2s ease",
                  }}
                  onMouseEnter={(e) => {
                    if (index !== currentIndex) {
                      (e.currentTarget as HTMLDivElement).style.backgroundColor =
                        theme.palette.border;
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (index !== currentIndex) {
                      (e.currentTarget as HTMLDivElement).style.backgroundColor =
                        theme.palette.surface;
                    }
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                    }}
                  >
                    <div style={{ flex: 1 }}>
                      <div
                        style={{
                          fontSize: "0.875rem",
                          fontWeight: 600,
                          color:
                            index === currentIndex
                              ? theme.palette.surface
                              : theme.palette.primary,
                          marginBottom: theme.spacing.xs,
                        }}
                      >
                        {eventTypeLabels[event.type][language]}
                      </div>
                      <div
                        style={{
                          fontSize: "0.75rem",
                          color:
                            index === currentIndex
                              ? "rgba(255, 255, 255, 0.8)"
                              : theme.palette.secondary,
                        }}
                      >
                        {new Date(event.timestamp).toLocaleTimeString(
                          language === "ar" ? "ar-SA" : "en-US"
                        )}
                      </div>
                    </div>
                    {event.severity && (
                      <div
                        style={{
                          width: "12px",
                          height: "12px",
                          borderRadius: "50%",
                          backgroundColor: getSeverityColor(event.severity),
                          marginRight: theme.spacing.md,
                        }}
                      />
                    )}
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        toggleExpand(event.id);
                      }}
                      style={{
                        background: "none",
                        border: "none",
                        cursor: "pointer",
                        padding: 0,
                        color:
                          index === currentIndex
                            ? theme.palette.surface
                            : theme.palette.primary,
                      }}
                    >
                      {isExpanded(event.id) ? (
                        <ChevronUp size={16} />
                      ) : (
                        <ChevronDown size={16} />
                      )}
                    </button>
                  </div>

                  <AnimatePresence>
                    {isExpanded(event.id) && (
                      <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: "auto" }}
                        exit={{ opacity: 0, height: 0 }}
                        transition={{ duration: 0.2 }}
                        style={{
                          marginTop: theme.spacing.md,
                          paddingTop: theme.spacing.md,
                          borderTop: `1px solid ${
                            index === currentIndex
                              ? "rgba(255, 255, 255, 0.2)"
                              : theme.palette.border
                          }`,
                        }}
                      >
                        <div
                          style={{
                            fontSize: "0.875rem",
                            lineHeight: 1.6,
                            color:
                              index === currentIndex
                                ? "rgba(255, 255, 255, 0.9)"
                                : theme.palette.primary,
                          }}
                        >
                          {event.description}
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
};
