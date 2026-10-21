// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import React, { useEffect } from 'react';
import { Crosshair, CheckCircle2, MapPin } from 'lucide-react';

interface MapAssociationBannerProps {
  isAssociatingSourceId: string | null;
  associationNotice: string | null;
  onCancelAssociation: () => void;
  isPickingElement?: boolean;
  pickingPrompt?: string | null;
  onCancelPicking?: () => void;
}

export const MapAssociationBanner: React.FC<MapAssociationBannerProps> = ({
  isAssociatingSourceId,
  associationNotice,
  onCancelAssociation,
  isPickingElement,
  pickingPrompt,
  onCancelPicking,
}) => {
  // Allow canceling picker or association with Escape key
  useEffect(() => {
    if (!isPickingElement && !isAssociatingSourceId) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        if (isPickingElement && onCancelPicking) {
          onCancelPicking();
        } else if (isAssociatingSourceId) {
          onCancelAssociation();
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isPickingElement, isAssociatingSourceId, onCancelPicking, onCancelAssociation]);

  return (
    <>
      {/* Element Picking Mode Banner (e.g. from Ingestion Wizard) */}
      {isPickingElement && (
        <div className="absolute top-4 left-1/2 -translate-x-1/2 z-30 glass-panel bg-primary-950/95 text-white px-5 py-3 rounded-2xl shadow-2xl flex items-center gap-4 border border-primary-500/60 animate-in slide-in-from-top-4 select-none">
          <div className="w-9 h-9 rounded-xl bg-primary-600/30 border border-primary-500/40 flex items-center justify-center flex-shrink-0">
            <MapPin className="w-5 h-5 text-accent-cyan animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <p className="text-xs font-bold text-white">Modo de Seleção no Mapa Ativo</p>
              <span className="text-[10px] bg-accent-cyan/20 text-accent-cyan px-2 py-0.5 rounded-full border border-accent-cyan/30 font-semibold">
                Assistente de Ingestão
              </span>
            </div>
            <p className="text-[11px] text-slate-300 mt-0.5">
              {pickingPrompt || 'Clique em qualquer via ou cruzamento no mapa para selecionar.'}
            </p>
          </div>
          <button
            type="button"
            onClick={onCancelPicking}
            className="ml-2 px-3 py-1.5 text-xs bg-white/10 hover:bg-white/20 text-slate-200 hover:text-white rounded-xl font-semibold transition-colors cursor-pointer flex items-center gap-1.5 whitespace-nowrap"
          >
            <span>Voltar ao Assistente</span>
            <kbd className="text-[10px] px-1 py-0.5 bg-black/40 rounded border border-white/10 font-mono">Esc</kbd>
          </button>
        </div>
      )}

      {/* Association Crosshair Mode Banner */}
      {isAssociatingSourceId && !isPickingElement && (
        <div className="absolute top-4 left-6 z-20 glass-panel bg-primary-600/90 text-white px-4 py-2.5 rounded-xl shadow-2xl flex items-center gap-3 border border-primary-400 animate-pulse select-none">
          <Crosshair className="w-5 h-5 text-accent-cyan" />
          <div>
            <p className="text-xs font-bold">Modo de Associação Espacial Ativo</p>
            <p className="text-[11px] opacity-90">
              Clique em qualquer via ou cruzamento no mapa para vincular o sensor <b>{isAssociatingSourceId}</b>.
            </p>
          </div>
          <button
            onClick={onCancelAssociation}
            className="ml-2 px-2.5 py-1 text-[11px] bg-black/40 hover:bg-black/60 rounded-lg font-semibold transition-colors cursor-pointer"
          >
            Cancelar
          </button>
        </div>
      )}

      {/* Association Success Notification */}
      {associationNotice && (
        <div className="absolute top-4 left-6 z-20 glass-panel bg-emerald-950/90 text-emerald-300 px-4 py-2.5 rounded-xl shadow-2xl flex items-center gap-2 border border-emerald-500/50 animate-in fade-in select-none">
          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          <span className="text-xs font-semibold">{associationNotice}</span>
        </div>
      )}
    </>
  );
};
