"use client";

/**
 * LossInducingBanner — Global warning banner for Decision Room.
 *
 * Shown at the top of DecisionRoomV2 when ANY action is classified
 * as LOSS_INDUCING. Impossible to miss. Red. Prominent.
 *
 * Phase 3 of Decision Trust Layer.
 */

interface LossInducingBannerProps {
  hasLossInducing: boolean;
  lossInducingCount: number;
  lossInducingActions: string[];
  warningBanner: string | null;
  locale?: "en" | "ar";
}

export function LossInducingBanner({
  hasLossInducing,
  lossInducingCount,
  lossInducingActions,
  warningBanner,
  locale = "en",
}: LossInducingBannerProps) {
  if (!hasLossInducing) return null;

  const isAr = locale === "ar";

  return (
    <div
      className="w-full px-4 py-3 bg-red-100 border-2 border-red-500 rounded-xl shadow-sm"
      role="alert"
      dir={isAr ? "rtl" : "ltr"}
    >
      <div className="flex items-start gap-3">
        <span className="text-2xl shrink-0">{"\u26A0\uFE0F"}</span>
        <div className="space-y-1">
          <p className="text-sm font-bold text-red-800">
            {isAr
              ? `تحذير: ${lossInducingCount} إجراء(ات) موصى بها قد تدمر القيمة`
              : `WARNING: ${lossInducingCount} recommended action(s) may destroy value`}
          </p>
          <p className="text-xs text-red-700">
            {warningBanner ??
              (isAr
                ? `راجع الإجراءات ${lossInducingActions.join("، ")} قبل المتابعة.`
                : `Review actions ${lossInducingActions.join(", ")} before proceeding.`)}
          </p>
        </div>
      </div>
    </div>
  );
}

export default LossInducingBanner;
