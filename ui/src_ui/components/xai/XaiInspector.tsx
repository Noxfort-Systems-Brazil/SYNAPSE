// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import React, { useState } from 'react';
import { useXaiStore, useReportStore } from '../../stores';
import { xaiService } from '../../services/api';
import { XaiHeaderControls } from './XaiHeaderControls';
import { XaiSemanticPanel } from './XaiSemanticPanel';
import { XaiAttributionChart } from './XaiAttributionChart';
import { XaiOfficialReportModal } from './XaiOfficialReportModal';
import { XaiResultItem, XaiAuditVerdict } from '../../types/xai';

export const XaiInspector: React.FC = () => {
  const { verdicts, xaiHistory } = useXaiStore();
  const { isReportModalOpen, openReportModal, closeReportModal } = useReportStore();

  const [isExplaining, setIsExplaining] = useState(false);

  // Initial dynamic fallback if no history exists yet
  const dynamicFallbackResult: XaiResultItem = React.useMemo(() => ({
    id: 'initial',
    type: 'AUDITOR',
    target: 'Consistência Física Global (Zero-Trust)',
    convergence_delta: 0.0012,
    semantic_text:
      'Sistema em monitoramento Zero-Trust. Clique em "Explicar Decisão Atual" para rodar a inferência de Integrated Gradients em tempo real.',
    attributions: [0.04, 0.08, 0.12, 0.18, 0.26, 0.35, 0.48, 0.62, 0.78, 0.88, 0.95, 1.0],
    timestamp: new Date().toLocaleTimeString(),
  }), []);

  const dynamicFallbackVerdict: XaiAuditVerdict = React.useMemo(() => ({
    safe: true,
    error: 0.012,
    threshold: 0.045,
    vector: [0.1, 0.2, 0.3, 0.4, 0.5, 0.7, 0.85, 0.95, 1.0],
    timestamp: new Date().toLocaleTimeString(),
  }), []);

  const selectedResult = xaiHistory[0] || dynamicFallbackResult;
  const latestVerdict = verdicts[0] || dynamicFallbackVerdict;

  const handleExplainDecision = async () => {
    setIsExplaining(true);
    try {
      await xaiService.explainGlobal();
    } catch (err) {
      console.error('Failed to trigger XAI explanation:', err);
    } finally {
      setTimeout(() => setIsExplaining(false), 800);
    }
  };

  return (
    <div className="h-[calc(100vh-4rem-2rem)] overflow-y-auto p-6 space-y-6 bg-background select-none">
      {/* 1. Header Control Bar */}
      <XaiHeaderControls
        isExplaining={isExplaining}
        onExplainDecision={handleExplainDecision}
        onOpenReport={() => openReportModal()}
      />

      {/* 2. Main Work Area: Executive Summary + Clean Attribution Chart */}
      <div className="space-y-6">
        <XaiSemanticPanel
          result={selectedResult}
          latestVerdict={latestVerdict}
        />
        <XaiAttributionChart
          attributions={selectedResult.attributions}
          featureNames={selectedResult.feature_names}
        />
      </div>

      {/* 3. Official Municipal XAI Report Modal */}
      <XaiOfficialReportModal
        isOpen={isReportModalOpen}
        onClose={closeReportModal}
        result={selectedResult}
      />
    </div>
  );
};
