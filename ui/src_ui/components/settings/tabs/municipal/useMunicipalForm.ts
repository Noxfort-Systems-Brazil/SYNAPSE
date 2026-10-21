// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import { useState, useRef } from 'react';
import { useMunicipalSettingsStore } from '../../../../stores/useMunicipalSettingsStore';

export function useMunicipalForm() {
  const settings = useMunicipalSettingsStore();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [form, setForm] = useState({
    cityHall: settings.cityHall,
    department: settings.department,
    authorityName: settings.authorityName,
    authorityRole: settings.authorityRole,
    registrationNumber: settings.registrationNumber,
    processPrefix: settings.processPrefix,
  });

  const [logoPreview, setLogoPreview] = useState<string | null>(settings.logoDataUrl);
  const [savedSuccess, setSavedSuccess] = useState(false);

  const handleLogoUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (event) => {
        const result = event.target?.result as string;
        setLogoPreview(result);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleRemoveLogo = () => {
    setLogoPreview(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleSave = () => {
    settings.updateSettings({
      ...form,
      logoDataUrl: logoPreview,
    });
    setSavedSuccess(true);
    setTimeout(() => setSavedSuccess(false), 2500);
  };

  const handleReset = () => {
    settings.resetToDefaults();
    const def = useMunicipalSettingsStore.getState();
    setForm({
      cityHall: def.cityHall,
      department: def.department,
      authorityName: def.authorityName,
      authorityRole: def.authorityRole,
      registrationNumber: def.registrationNumber,
      processPrefix: def.processPrefix,
    });
    setLogoPreview(def.logoDataUrl);
    setSavedSuccess(true);
    setTimeout(() => setSavedSuccess(false), 2500);
  };

  return {
    form,
    setForm,
    logoPreview,
    savedSuccess,
    fileInputRef,
    handleLogoUpload,
    handleRemoveLogo,
    handleSave,
    handleReset,
  };
}
