import React, { useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useQuery } from '@tanstack/react-query';
import { fetcher } from '../api/client';

interface PersonSummary {
  id: string;
  name: string;
  party: string;
  constituency: string;
  role?: string | null;
  photo_url?: string | null;
  speech_count: number;
}

interface PersonListResponse {
  data: PersonSummary[];
  meta: {
    total: number;
    page: number;
    page_size: number;
  };
}

export default function Home() {
  const [query, setQuery] = useState('');
  const navigate = useNavigate();

  const { data, error, isLoading } = useQuery<PersonListResponse, Error>({
    queryKey: ['featured-persons'],
    queryFn: () => fetcher('/api/persons?page=1&page_size=8&sort=speech_count_desc'),
    staleTime: 60000,
    retry: false,
  });

  const mpCount = data?.meta.total ?? 0;
  const speechCount = useMemo(
    () => data?.data.reduce((sum, person) => sum + person.speech_count, 0) ?? 0,
    [data],
  );

  const featured = data?.data ?? [];

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const trimmed = query.trim();
    if (trimmed) {
      navigate(`/search?q=${encodeURIComponent(trimmed)}`);
    }
  };

  return (
    <main className="mx-auto flex w-full max-w-7xl flex-col gap-16 px-6 pb-20 pt-10 text-slate-100 sm:px-8">
      <section className="grid gap-10 lg:grid-cols-[1.1fr_0.9fr] lg:items-center">
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, ease: 'easeOut' }}
          className="space-y-8"
        >
          <div className="inline-flex items-center gap-2 rounded-full border border-amber-400/25 bg-amber-400/10 px-4 py-2 text-sm text-amber-200">
            Public parliamentary intelligence
          </div>

          <div className="space-y-6">
            <h1 className="max-w-3xl text-5xl font-semibold tracking-tight text-white sm:text-6xl">
              What did they actually say?
            </h1>
            <p className="max-w-2xl text-lg leading-8 text-slate-300">
              Search debates, compare MP positions, and surface source-backed evidence from UK parliamentary records.
            </p>
          </div>

          <form onSubmit={handleSubmit} className="grid gap-3 sm:grid-cols-[1fr_auto]">
            <label htmlFor="site-search" className="sr-only">
              Search parliamentary debate
            </label>
            <input
              id="site-search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search MPs, claims, debates, or keywords"
              className="min-h-[56px] rounded-3xl border border-[#1E2A45] bg-[#131A2E] px-5 text-lg text-slate-100 outline-none transition focus:border-amber-400/70 focus:ring-2 focus:ring-amber-400/25"
            />
            <button
              type="submit"
              className="min-h-[56px] rounded-3xl bg-amber-400 px-6 text-sm font-semibold text-slate-950 transition hover:bg-amber-300"
            >
              Search the chamber
            </button>
          </form>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="rounded-[2rem] border border-[#1E2A45] bg-[#131A2E]/80 p-6">
              <p className="text-sm uppercase tracking-[0.24em] text-amber-300/80">MPs tracked</p>
              <p className="mt-3 text-3xl font-semibold text-white">{mpCount.toLocaleString()}</p>
            </div>
            <div className="rounded-[2rem] border border-[#1E2A45] bg-[#131A2E]/80 p-6">
              <p className="text-sm uppercase tracking-[0.24em] text-amber-300/80">Speeches indexed</p>
              <p className="mt-3 text-3xl font-semibold text-white">{speechCount.toLocaleString()}</p>
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.96 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.7, delay: 0.1, ease: 'easeOut' }}
          className="rounded-[2rem] border border-[#1E2A45] bg-[#131A2E]/80 p-8 shadow-glow"
        >
          <p className="text-sm uppercase tracking-[0.24em] text-amber-300/80">Featured politicians</p>
          <p className="mt-4 text-3xl font-semibold text-white">The most active voices in the chamber.</p>
          <p className="mt-4 text-slate-400">
            Explore a sample of MPs with the highest recorded speech volume and the strongest debate footprint.
          </p>
        </motion.div>
      </section>

      <section className="space-y-8">
        <div className="flex items-center justify-between gap-6">
          <div>
            <p className="text-sm uppercase tracking-[0.24em] text-amber-300/80">Featured MPs</p>
            <h2 className="mt-3 text-3xl font-semibold text-white">Profiles surfaced from Hansard.</h2>
          </div>
          <Link
            to="/search"
            className="rounded-full border border-[#1E2A45] bg-[#131A2E]/80 px-5 py-3 text-sm text-slate-200 transition hover:border-amber-400/50 hover:text-white"
          >
            Browse all MPs
          </Link>
        </div>

        {isLoading ? (
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="h-52 rounded-[2rem] bg-[#131A2E]/80" />
            <div className="h-52 rounded-[2rem] bg-[#131A2E]/80" />
            <div className="h-52 rounded-[2rem] bg-[#131A2E]/80" />
            <div className="h-52 rounded-[2rem] bg-[#131A2E]/80" />
          </div>
        ) : error ? (
          <div className="rounded-[2rem] border border-[#1E2A45] bg-[#131A2E]/80 p-8 text-slate-300">
            Unable to load featured MPs. Please refresh the page.
          </div>
        ) : (
          <div className="grid gap-6 xl:grid-cols-2">
            {featured.map((person) => (
              <Link
                key={person.id}
                to={`/person/${person.id}`}
                className="group rounded-[2rem] border border-[#1E2A45] bg-[#131A2E]/80 p-6 transition hover:border-amber-400/50"
              >
                <div className="flex items-center justify-between gap-4">
                  <div>
                    <p className="text-sm uppercase tracking-[0.24em] text-amber-300/80">{person.party}</p>
                    <h3 className="mt-3 text-2xl font-semibold text-white">{person.name}</h3>
                    <p className="mt-2 text-sm text-slate-400">{person.constituency}</p>
                  </div>
                  <div className="rounded-3xl bg-slate-950/80 px-4 py-3 text-right text-sm">
                    <p className="text-slate-400">Speeches</p>
                    <p className="mt-2 text-xl font-semibold text-white">{person.speech_count}</p>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </section>

      <section className="grid gap-6 rounded-[2rem] border border-[#1E2A45] bg-[#131A2E]/80 p-10 shadow-glow lg:grid-cols-[1.1fr_0.9fr]">
        <div className="space-y-5">
          <p className="text-sm uppercase tracking-[0.24em] text-amber-300/80">Why Echo</p>
          <h2 className="text-3xl font-semibold text-white sm:text-4xl">
            Evidence-led research for UK politics.
          </h2>
          <p className="max-w-xl text-slate-400">
            Echo surfaces claim context, speaker histories, and source-backed statements from parliamentary transcripts so you can build reporting with confidence.
          </p>
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="rounded-[2rem] border border-[#1E2A45] bg-[#0D141F]/80 p-6">
            <p className="text-sm uppercase tracking-[0.24em] text-amber-300/80">Search</p>
            <p className="mt-3 text-lg font-semibold text-white">Find the exact quote in Hansard.</p>
          </div>
          <div className="rounded-[2rem] border border-[#1E2A45] bg-[#0D141F]/80 p-6">
            <p className="text-sm uppercase tracking-[0.24em] text-amber-300/80">Compare</p>
            <p className="mt-3 text-lg font-semibold text-white">Review MPs and positions side by side.</p>
          </div>
        </div>
      </section>
    </main>
  );
}
