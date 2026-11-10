// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import React from 'react';
import { PeritialQuesitoItem } from '../../../types/report';
import { ReportAuditFindingsCard } from './ReportAuditFindingsCard';

interface ReportQuesitosCardProps {
  quesitos?: PeritialQuesitoItem[];
}

/**
 * Standardized replacement for the legacy Q&A Quesitos card.
 * Renders affirmative forensic pericial findings in strict ABNT NBR 10719:2015 format.
 */
export const ReportQuesitosCard: React.FC<ReportQuesitosCardProps> = () => {
  return <ReportAuditFindingsCard />;
};
