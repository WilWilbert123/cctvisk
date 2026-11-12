import React from 'react';
import { CheckCircle2 } from 'lucide-react';
import type { RecoveryStepItem } from '../../types/recovery';

interface RecoveryStepsProps {
  steps: Array<RecoveryStepItem | string>;
}

export const RecoverySteps: React.FC<RecoveryStepsProps> = ({ steps }) => {
  return (
    <div className="space-y-2.5">
      <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
        Step-by-Step Authorized Recovery Workflow
      </h4>
      <div className="space-y-2">
        {steps.map((step, index) => {
          const isString = typeof step === 'string';
          const num = isString ? index + 1 : step.step_number || index + 1;
          const title = isString ? `Step ${num}` : step.title;
          const desc = isString ? step : step.description;

          return (
            <div
              key={num}
              className="flex items-start gap-3 p-3.5 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800"
            >
              <div className="w-6 h-6 rounded-full bg-blue-600 text-white text-xs font-bold flex items-center justify-center shrink-0 mt-0.5">
                {num}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                  {title}
                </p>
                <p className="text-xs text-slate-600 dark:text-slate-300 mt-0.5 leading-relaxed">
                  {desc}
                </p>
              </div>
              <CheckCircle2 className="w-4 h-4 text-slate-300 dark:text-slate-700 shrink-0 mt-1" />
            </div>
          );
        })}
      </div>
    </div>
  );
};
