export function base64ToBlob(base64: string, mime = "audio/wav"): Blob {
  const bytes = atob(base64);
  const arr = new Uint8Array(bytes.length);
  for (let i = 0; i < bytes.length; i++) arr[i] = bytes.charCodeAt(i);
  return new Blob([arr], { type: mime });
}

/** Plays a sequence of base64-encoded WAV clips back-to-back. Resolves
 * when playback finishes or is stopped. Returns a stop() function the
 * caller can use to cancel mid-playback. */
export function playClipsSequentially(clips: string[]): { done: Promise<void>; stop: () => void } {
  let cancelled = false;
  let currentAudio: HTMLAudioElement | null = null;

  const done = (async () => {
    for (const clip of clips) {
      if (cancelled) return;
      const url = URL.createObjectURL(base64ToBlob(clip));
      const audio = new Audio(url);
      currentAudio = audio;
      try {
        await new Promise<void>((resolve, reject) => {
          audio.onended = () => resolve();
          audio.onerror = () => reject(new Error("Audio playback failed"));
          if (cancelled) resolve();
          else audio.play().catch(reject);
        });
      } finally {
        URL.revokeObjectURL(url);
      }
      if (cancelled) return;
    }
  })();

  const stop = () => {
    cancelled = true;
    currentAudio?.pause();
  };

  return { done, stop };
}
