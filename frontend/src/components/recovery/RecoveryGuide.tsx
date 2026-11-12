import React from 'react';
import { ShieldAlert, Wrench, HelpCircle, RotateCcw } from 'lucide-react';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { RecoverySteps } from './RecoverySteps';
import type { ManufacturerRecoveryGuide } from '../../types/recovery';

interface RecoveryGuideProps {
  guide: ManufacturerRecoveryGuide;
}

export const RecoveryGuide: React.FC<RecoveryGuideProps> = ({ guide }) => {
  return (
    <div className="space-y-4">
      <Card
        title={`${guide.display_name || guide.manufacturer} — Official Recovery Procedure`}
        subtitle="Authorized manufacturer reset and recovery workflow (Zero exploit/brute-force policy)"
        action={<Badge variant="info">{guide.manufacturer}</Badge>}
      >
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 rounded-xl bg-blue-50/60 dark:bg-blue-950/30 border border-blue-200/70 dark:border-blue-900/50 space-y-2">
              <div className="flex items-center gap-2 text-xs font-semibold text-blue-800 dark:text-blue-300">
                <Wrench className="w-4 h-4" />
                <span>Official Vendor Utilities</span>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {(guide.official_tools || []).map((tool) => (
                  <Badge key={tool} variant="info">
                    {tool}
                  </Badge>
                ))}
              </div>
              <p className="text-xs text-slate-600 dark:text-slate-400 pt-1">
                {guide.official_support_info}
              </p>
            </div>

            <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-800 space-y-2">
              <div className="flex items-center gap-2 text-xs font-semibold text-slate-800 dark:text-slate-200">
                <RotateCcw className="w-4 h-4 text-emerald-600" />
                <span>Hardware / Physical Reset Procedure</span>
              </div>
              <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
                {guide.physical_reset_procedure}
              </p>
            </div>
          </div>

          <RecoverySteps steps={guide.steps || []} />

          {guide.warnings && guide.warnings.length > 0 && (
            <div className="p-4 rounded-xl bg-amber-50/70 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800/70 space-y-2">
              <div className="flex items-center gap-2 text-xs font-semibold text-amber-800 dark:text-amber-300">
                <ShieldAlert className="w-4 h-4" />
                <span>Important Recovery Warnings &amp; Precautions</span>
              </div>
              <ul className="list-disc list-inside text-xs text-amber-900 dark:text-amber-200 space-y-1">
                {guide.warnings.map((warn, i) => (
                  <li key={i}>{warn}</li>
                ))}
              </ul>
            </div>
          )}

          {guide.default_network_behavior && (
            <div className="flex items-start gap-2.5 text-xs text-slate-600 dark:text-slate-400 bg-slate-50 dark:bg-slate-800/40 p-3 rounded-lg">
              <HelpCircle className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
              <span>
                <strong>Post-Reset Network Behavior:</strong>{' '}
                {guide.default_network_behavior}
              </span>
            </div>
          )}
        </div>
      </Card>
    </div>
  );
};
