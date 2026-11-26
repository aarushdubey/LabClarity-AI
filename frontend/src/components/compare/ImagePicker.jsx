/** Searchable image list for Compare: shows result counts, upload time and project, so
 * duplicate file names are distinguishable and images without results are obvious. */
import { Search } from 'lucide-react';
import { useState } from 'react';
import { assetUrl } from '../../api/imageApi.js';
import { timeAgo } from '../../utils/format.js';
import { Badge } from '../common/Badge.jsx';
import { SkeletonGrid } from '../common/Skeleton.jsx';

export function ImagePicker({ images, value, onSelect }) {
  const [query, setQuery] = useState('');
  const q = query.trim().toLowerCase();
  const shown = (images ?? []).filter((a) => !q || a.originalName.toLowerCase().includes(q));
  const withResults = (images ?? []).filter((a) => a.resultCount > 0).length;

  return (
    <div>
      <label className="relative mb-2 block">
        <Search className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-slate-500" aria-hidden />
        <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search images" aria-label="Search images" className="h-9 w-full rounded-lg border border-line bg-ink-950/60 pr-3 pl-9 text-sm text-slate-100 focus:border-brand-400/60 focus:outline-none" />
      </label>
      {images && <p className="mb-2 text-xs text-slate-500">{withResults} of {images.length} images have results to compare.</p>}
      {!images && <SkeletonGrid count={5} className="space-y-2" item="h-14" />}
      <ul className="max-h-[540px] space-y-1.5 overflow-y-auto pr-1">
        {shown.map((a) => {
          const active = a.id === value;
          return (
            <li key={a.id}>
              <button
                type="button"
                onClick={() => onSelect(a.id)}
                aria-pressed={active}
                className={`flex w-full items-center gap-3 rounded-xl border p-2 text-left transition-all duration-200
                  ${active ? 'border-brand-400/50 bg-brand-400/8' : 'border-transparent hover:border-line hover:bg-white/[0.03]'}
                  ${a.resultCount ? '' : 'opacity-70'}`}
              >
                <img src={assetUrl(a.links.preview)} alt="" className="checkerboard size-10 shrink-0 rounded-lg object-cover" />
                <span className="min-w-0 flex-1">
                  <span className="block truncate text-sm text-slate-200" title={a.originalName}>{a.originalName}</span>
                  <span className="mt-0.5 flex flex-wrap items-center gap-1.5 text-[11px] text-slate-500">
                    {a.resultCount ? <Badge tone="success">{a.resultCount} result{a.resultCount === 1 ? '' : 's'}</Badge> : <Badge>No results yet</Badge>}
                    <span>{timeAgo(a.createdAt)}</span>
                    {a.experimentId && <span>· in project</span>}
                  </span>
                </span>
              </button>
            </li>
          );
        })}
      </ul>
      {images && shown.length === 0 && <p className="py-4 text-center text-sm text-slate-500">No images match “{query}”.</p>}
    </div>
  );
}
