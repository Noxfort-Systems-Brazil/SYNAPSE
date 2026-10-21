// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import React, { useMemo } from 'react';
import katex from 'katex';

interface LatexRendererProps {
  math: string;
  displayMode?: boolean;
  className?: string;
}

/**
 * Reusable LaTeX mathematical renderer leveraging KaTeX.
 * Handles display equations (block) and inline formulas cleanly for HTML and PDF rendering.
 */
export const LatexRenderer: React.FC<LatexRendererProps> = ({
  math,
  displayMode = true,
  className = '',
}) => {
  const html = useMemo(() => {
    try {
      return katex.renderToString(math, {
        displayMode,
        throwOnError: false,
        output: 'html', // Output pure HTML to avoid MathML artifacts in html2canvas
        strict: false,
      });
    } catch (e) {
      console.error('KaTeX rendering error:', e);
      return math;
    }
  }, [math, displayMode]);

  return (
    <span
      className={`katex-renderer select-none ${className}`}
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
};
