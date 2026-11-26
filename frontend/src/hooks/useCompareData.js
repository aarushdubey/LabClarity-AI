/**
 * Data for the Compare page. Results are always tied to the image they belong to, so switching
 * images never shows (or auto-selects) the previous image's runs while the new ones load.
 */
import { useEffect, useMemo, useState } from 'react';
import { getRun, listAssets, listRuns, listRunsPage } from '../api/researchApi.js';

export const MAX_SELECTED = 6;

/** Pages through completed runs (the API caps a page at 100) so per-image counts are exact. */
async function allCompletedRuns(signal, maxPages = 20) {
  const all = [];
  for (let page = 1; page <= maxPages; page += 1) {
    const { data, meta } = await listRunsPage({ status: 'completed', limit: 100, page }, signal);
    all.push(...(data ?? []));
    if (!meta || all.length >= meta.total || !data?.length) break;
  }
  return all;
}

/** All images plus how many completed results each has (images with results first). */
export function useImageCatalog(refreshKey) {
  const [state, setState] = useState({ images: null, error: null });
  useEffect(() => {
    const controller = new AbortController();
    Promise.all([listAssets(controller.signal), allCompletedRuns(controller.signal)])
      .then(([assets, runs]) => {
        const counts = runs.reduce((m, r) => ({ ...m, [r.assetId]: (m[r.assetId] ?? 0) + 1 }), {});
        const images = assets
          .map((a) => ({ ...a, resultCount: counts[a.id] ?? 0 }))
          .sort((a, b) => (b.resultCount > 0) - (a.resultCount > 0) || new Date(b.createdAt) - new Date(a.createdAt));
        setState({ images, error: null });
      })
      .catch((err) => err.name !== 'AbortError' && setState({ images: [], error: err }));
    return () => controller.abort();
  }, [refreshKey]);
  return state;
}

/** Completed runs of one image, the selection, and full records of the selected runs. */
export function useImageRuns(assetId) {
  const [runs, setRuns] = useState({ assetId: null, items: null, error: null });
  const [selected, setSelected] = useState([]);
  const [details, setDetails] = useState({});

  useEffect(() => {
    setSelected([]);
    if (!assetId) return undefined;
    const controller = new AbortController();
    setRuns({ assetId, items: null, error: null });
    listRuns({ assetId, status: 'completed', limit: 50 }, controller.signal)
      .then((items) => {
        setRuns({ assetId, items, error: null });
        setSelected(items.slice(0, 3).map((r) => r.id));
      })
      .catch((err) => err.name !== 'AbortError' && setRuns({ assetId, items: [], error: err }));
    return () => controller.abort();
  }, [assetId]);

  useEffect(() => {
    const missing = selected.filter((id) => !details[id]);
    if (!missing.length) return undefined;
    const controller = new AbortController();
    Promise.all(missing.map((id) => getRun(id, controller.signal)))
      .then((loaded) => setDetails((d) => ({ ...d, ...Object.fromEntries(loaded.map((r) => [r.id, r])) })))
      .catch(() => {});
    return () => controller.abort();
  }, [selected, details]);

  const current = runs.assetId === assetId ? runs : { items: null, error: null };
  const compared = useMemo(
    () => selected.map((id) => details[id]).filter((r) => r && r.assetId === assetId),
    [selected, details, assetId],
  );
  const toggle = (id) =>
    setSelected((s) => (s.includes(id) ? s.filter((x) => x !== id) : s.length < MAX_SELECTED ? [...s, id] : s));

  return {
    runs: current.items, error: current.error, selected, toggle, compared,
    loadingDetails: selected.length > 0 && compared.length < selected.length,
  };
}
