import { CheckSquare, Square, Wand2 } from 'lucide-react';
import { Link, useSearchParams } from 'react-router';
import { ComparisonGrid } from '../components/batch/ComparisonGrid.jsx';
import { ComparisonTable } from '../components/batch/ComparisonTable.jsx';
import { Button } from '../components/common/Button.jsx';
import { Panel } from '../components/common/Panel.jsx';
import { SkeletonGrid } from '../components/common/Skeleton.jsx';
import { ImagePicker } from '../components/compare/ImagePicker.jsx';
import { Reveal } from '../components/motion/Reveal.jsx';
import { MAX_SELECTED, useImageCatalog, useImageRuns } from '../hooks/useCompareData.js';

/** Pick a source image, then any of its completed runs, and compare them side by side. */
export function ComparePage() {
  const [params, setParams] = useSearchParams();
  const assetId = params.get('image') ?? '';
  const { images, error: catalogError } = useImageCatalog();
  const { runs, error, selected, toggle, compared, loadingDetails } = useImageRuns(assetId);
  const image = images?.find((a) => a.id === assetId);
  const enhanceLink = assetId ? `/enhance?image=${encodeURIComponent(assetId)}` : '/enhance';

  return (
    <main className="mx-auto max-w-[1440px] space-y-6 px-4 py-8 sm:px-6">
      <Reveal as="header" className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white">Compare</h1>
          <p className="mt-1 text-sm text-slate-400">Choose an image, then the runs to compare: synchronised zoom and pan, plus metrics side by side.</p>
        </div>
        <Button as={Link} to={enhanceLink} variant="secondary" icon={Wand2}>New comparison run</Button>
      </Reveal>

      <div className="grid gap-6 lg:grid-cols-[340px_minmax(0,1fr)]">
        <Panel title="1. Source image" className="h-fit">
          {catalogError && <p className="mb-2 text-sm text-rose-300">Could not load images: {catalogError.message}</p>}
          {images?.length === 0 && !catalogError && (
            <p className="text-sm text-slate-500">No images yet. <Link to={enhanceLink} className="text-brand-300 hover:underline">Upload one</Link>.</p>
          )}
          <ImagePicker images={images} value={assetId} onSelect={(id) => setParams({ image: id })} />
        </Panel>

        <div className="space-y-6">
          <Panel title="2. Runs to compare" subtitle={`Select up to ${MAX_SELECTED}${selected.length ? ` · ${selected.length} selected` : ''}`}>
            {!assetId && <p className="text-sm text-slate-500">Choose a source image on the left. Images marked “No results yet” have not been processed.</p>}
            {assetId && !runs && !error && <SkeletonGrid count={3} className="flex gap-2" item="h-8 w-28" />}
            {error && <p className="text-sm text-rose-300">Could not load results: {error.message}</p>}
            {runs?.length === 0 && (
              <div className="rounded-xl border border-dashed border-line p-4 text-sm text-slate-400">
                <p><span className="font-medium text-slate-200">{image?.originalName ?? 'This image'}</span> has no completed results yet, so there is nothing to compare.</p>
                <p className="mt-1">Open Enhance, run two or more pipelines on it (e.g. classical vs AI), then come back here.</p>
                <Button as={Link} to={enhanceLink} size="sm" icon={Wand2} className="mt-3">Process in Enhance</Button>
              </div>
            )}
            {runs?.length === 1 && <p className="mb-2 text-xs text-slate-500">Only one result so far; run another pipeline in Enhance to compare against it.</p>}
            <div className="flex flex-wrap gap-2">
              {(runs ?? []).map((r) => {
                const on = selected.includes(r.id);
                const full = !on && selected.length >= MAX_SELECTED;
                const Icon = on ? CheckSquare : Square;
                return (
                  <button key={r.id} type="button" onClick={() => toggle(r.id)} aria-pressed={on} disabled={full}
                    title={full ? `At most ${MAX_SELECTED} runs can be compared` : undefined}
                    className={`inline-flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs font-medium transition-all duration-200 active:scale-[0.97] disabled:cursor-not-allowed disabled:opacity-40 ${on ? 'border-brand-400/50 bg-brand-400/10 text-brand-300' : 'border-line text-slate-300 hover:border-brand-400/30'}`}>
                    <Icon className="size-3.5" aria-hidden /> {r.label ?? r.model}
                  </button>
                );
              })}
            </div>
            {runs?.length > 0 && selected.length === 0 && <p className="mt-3 text-xs text-slate-500">Select at least one result to show it.</p>}
          </Panel>
          {loadingDetails && compared.length === 0 && <SkeletonGrid count={2} className="grid gap-4 sm:grid-cols-2" item="h-64" />}
          {compared.length > 0 && (
            <>
              <Panel title="Side-by-side"><ComparisonGrid runs={compared} /></Panel>
              <Panel title="Metrics"><ComparisonTable runs={compared} /></Panel>
            </>
          )}
        </div>
      </div>
    </main>
  );
}
