import React, { useEffect, useMemo, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
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
  claim_count: number;
}

interface PersonListResponse {
  data: PersonSummary[];
  meta: {
    total: number;
    page: number;
    page_size: number;
  };
}

export default function Search() {
  const [searchParams, setSearchParams] = useSearchParams();
  const query = searchParams.get('q')?.trim() ?? '';
  const [searchText, setSearchText] = useState(query);

  useEffect(() => {
    setSearchText(query);
  }, [query]);

  useEffect(() => {
    const timeout = setTimeout(() => {
      const normalized = searchText.trim();
      if (normalized !== query) {
        if (normalized) {
          setSearchParams({ q: normalized });
        } else {
          setSearchParams({});
        }
      }
    }, 300);

    return () => clearTimeout(timeout);
  }, [query, searchText, setSearchParams]);

  const {
    data,
    error,
    isLoading,
  } = useQuery<PersonListResponse, Error>({
    queryKey: ['search-persons', query],
    queryFn: () =>
      fetcher(
        query.length > 0
          ? `/api/persons?search=${encodeURIComponent(query)}&page=1&page_size=100&sort=speech_count_desc`
          : `/api/persons?page=1&page_size=100&sort=speech_count_desc`,
      ),
    enabled: true,
    staleTime: 60000,
    retry: false,
  });

  const visiblePersons = useMemo(() => {
    const persons = data?.data ?? [];
    if (query.length === 0) {
      // Browse all MPs - show only those with speeches, sorted by speech count
      return [...persons]
        .filter((person) => person.speech_count > 0)
        .sort((a, b) => b.speech_count - a.speech_count);
    }
    // When searching, show MPs with data first, then others
    return [...persons].sort((a, b) => {
      if (a.speech_count > 0 && b.speech_count === 0) return -1;
      if (a.speech_count === 0 && b.speech_count > 0) return 1;
      return b.speech_count - a.speech_count;
    });
  }, [data?.data, query]);

  const resultLabel = query.length
    ? `Found ${visiblePersons.length} MP${visiblePersons.length === 1 ? '' : 's'} matching '${query}'`
    : `Showing ${visiblePersons.length} MP${visiblePersons.length === 1 ? '' : 's'} with parliamentary data`;

  return (
    <main className="mx-auto flex w-full max-w-7xl flex-col gap-10 px-6 pb-16 pt-10 text-slate-100 sm:px-8">
      <section className="rounded-[2rem] border border-[#1E2A45] bg-[#131A2E]/80 p-10 shadow-glow">
        <p className="text-sm uppercase tracking-[0.24em] text-amber-300/80">Search</p>
        <h1 className="mt-4 text-4xl font-semibold text-white">Explore MPs, claims, and parliamentary language.</h1>
        <p className="mt-4 text-slate-400">
          Search by name, party, or issue to find matching MPs and the evidence behind their positions.
        </p>

        <form
          onSubmit={(event) => {
            event.preventDefault();
            const normalized = searchText.trim();
            if (normalized) {
              setSearchParams({ q: normalized });
            } else {
              setSearchParams({});
            }
          }}
          className="mt-8"
        >
          <label htmlFor="search" className="sr-only">
            Search MPs, claims, and keywords
          </label>
          <input
            id="search"
            type="search"
            value={searchText}
            onChange={(event) => setSearchText(event.target.value)}
            placeholder="Search MPs, claims, or policy keywords"
            className="w-full rounded-3xl border border-[#1E2A45] bg-[#131A2E] px-5 py-4 text-lg text-slate-100 outline-none transition focus:border-amber-400/70 focus:ring-2 focus:ring-amber-400/25"
          />
        </form>
      </section>

      <section className="space-y-6">
        <div className="flex flex-col gap-2 rounded-[2rem] border border-[#1E2A45] bg-[#0D141F]/80 p-6">
          <p className="text-sm uppercase tracking-[0.24em] text-amber-300/80">{query.length ? 'Search results' : 'Browse all MPs'}</p>
          <p className="text-xl font-semibold text-white">{resultLabel}</p>
        </div>

        {isLoading ? (
          <div className="rounded-[2rem] border border-[#1E2A45] bg-[#131A2E]/80 p-10 text-slate-300">Loading MPs…</div>
        ) : error ? (
          <div className="rounded-[2rem] border border-[#1E2A45] bg-[#131A2E]/80 p-10 text-slate-300">
            Search failed. Please refresh or try again.
          </div>
        ) : visiblePersons.length === 0 ? (
          <div className="rounded-[2rem] border border-[#1E2A45] bg-[#131A2E]/80 p-10 text-slate-300">
            {query.length
              ? `No MPs matched "${query}". Try a broader keyword.`
              : 'No parliamentary MPs found yet.'}
          </div>
        ) : (
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
            className="grid gap-6 sm:grid-cols-2 xl:grid-cols-3"
          >
            {visiblePersons.map((person) => (
              <Link
                key={person.id}
                to={`/person/${person.id}`}
                className={`group overflow-hidden rounded-[2rem] border border-[#1E2A45] bg-[#131A2E]/80 p-6 transition duration-200 hover:-translate-y-1 hover:border-amber-400/70 hover:shadow-[0_20px_60px_rgba(250,204,21,0.16)] ${
                  query.length > 0 && person.speech_count === 0 ? 'opacity-50' : ''
                }`}
              >
                <div className="flex items-center gap-4">
                  <div className="flex h-16 w-16 items-center justify-center overflow-hidden rounded-[1.5rem] bg-[#0D141F]/80">
                    {person.photo_url ? (
                      <img src={person.photo_url} alt={person.name} className="h-full w-full object-cover" />
                    ) : (
                      <span className="text-sm text-slate-400">No photo</span>
                    )}
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm uppercase tracking-[0.24em] text-amber-300/80">{person.party}</p>
                    <h2 className="mt-2 truncate text-2xl font-semibold text-white">{person.name}</h2>
                  </div>
                </div>
                <p className="mt-4 text-sm text-slate-400">{person.constituency}</p>
                <div className="mt-5 grid gap-3 sm:grid-cols-2">
                  <div className="rounded-[1.5rem] bg-[#0D141F]/80 p-4 text-sm text-slate-300">
                    <p className="text-xs uppercase tracking-[0.24em] text-amber-300/80">Speeches</p>
                    <p className="mt-2 text-lg font-semibold text-white">{person.speech_count}</p>
                  </div>
                  <div className="rounded-[1.5rem] bg-[#0D141F]/80 p-4 text-sm text-slate-300">
                    <p className="text-xs uppercase tracking-[0.24em] text-amber-300/80">Claims</p>
                    <p className="mt-2 text-lg font-semibold text-white">{person.claim_count}</p>
                  </div>
                </div>
              </Link>
            ))}
          </motion.div>
        )}
      </section>
    </main>
  );
}
