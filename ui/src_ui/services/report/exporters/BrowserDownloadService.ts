// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

/**
 * Encapsulates low-level browser DOM and clipboard download operations (SRP & DIP).
 */
export class BrowserDownloadService {
  public static async copyToClipboard(text: string): Promise<boolean> {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch {
      return false;
    }
  }

  public static print(): void {
    window.print();
  }

  public static downloadBlob(blob: Blob, filename: string): void {
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }

  public static downloadMarkdown(filename: string, content: string): void {
    const blob = new Blob([content], { type: 'text/markdown;charset=utf-8;' });
    this.downloadBlob(blob, filename);
  }

  /**
   * Attempts saving via Tauri Desktop Native File Dialog, falling back to
   * Web File System Access API, and finally browser anchor download.
   */
  public static async saveWithPlatformBridge(
    cleanFilename: string,
    title: string,
    filterName: string,
    filterExtensions: string[],
    base64DataUri: string,
    blobFallback: Blob,
    mimeType: string
  ): Promise<boolean> {
    // 1. Check Tauri Desktop Native Dialog
    try {
      const { invoke } = await import('@tauri-apps/api/core');
      const chosenPath = await invoke<string | null>('save_file_dialog', {
        defaultFilename: cleanFilename,
        title,
        filterName,
        filterExtensions,
      });

      if (!chosenPath) {
        return false;
      }

      await invoke('write_file_bytes', {
        filePath: chosenPath,
        base64Content: base64DataUri,
      });

      return true;
    } catch {
      // Not running inside Tauri or IPC failed
    }

    // 2. Web fallback: File System Access API
    if ('showSaveFilePicker' in window) {
      try {
        const pickerOptions = {
          suggestedName: cleanFilename,
          types: [
            {
              description: filterName,
              accept: { [mimeType]: filterExtensions.map((ext) => `.${ext}`) },
            },
          ],
        };

        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const fileHandle = await (window as any).showSaveFilePicker(pickerOptions);
        const writable = await fileHandle.createWritable();
        await writable.write(blobFallback);
        await writable.close();
        return true;
      } catch (pickerErr: unknown) {
        if (pickerErr instanceof Error && pickerErr.name === 'AbortError') {
          return false;
        }
      }
    }

    // 3. Fallback: Browser download trigger
    this.downloadBlob(blobFallback, cleanFilename);
    return true;
  }
}
