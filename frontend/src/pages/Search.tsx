import React from 'react';
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

export default function Search() {
  const [searchParams] = useSearchParams();
  const query = searchParams.get('q')?.trim() ?? '';

  const { data, error, isLoading } = useQuery<PersonListResponse, Error>({
    queryKey: ['search-persons', query],
    queryFn: () => fetcher(`/api/persons?search=${encodeURIComponent(query)}&page=1&page_size=12`),
    enabled: query.length > 0,
    staleTime: 60000,
    retry: false,
  });

  return (
    <main className="mx-auto flex w-full max-w-6xl flex-col gap-10 px-6 pb-16 pt-10 text-slate-100 sm:px-8">
      <section className="rounded-[2rem] border border-[#1E2A45] bg-[#131A2E]/80 p-10 shadow-glow">
        <p className="text-sm uppercase tracking-[0.24em] text-amber-300/80">Search</p>
        <h1 className="mt-4 text-4xl font-semibold text-white">Explore parliamentary language and MP positions.</h1>
        <p className="mt-4 text-slate-400">
          Enter a name, topic, or claim to find matching MPs and the speeches they appear in.
        </p>
      </section>

      <section className="space-y-6">
        {query.length === 0 ? (
          <div className="rounded-[2rem] border border-[#1E2A45] bg-[#131A2E]/80 p-10 text-slate-300">
            Start with a query in the search bar, for example "climate change" or "health funding".
          </div>
        ) : isLoading ? (
          <div className="rounded-[2rem] border border-[#1E2A45] bg-[#131A2E]/80 p-10 text-slate-300">Searching…</div>
        ) : error ? (
          <div className="rounded-[2rem] border border-[#1E2A45] bg-[#131A2E]/80 p-10 text-slate-300">
            Search failed. Please try again.
          </div>
        ) : data?.data.length ? (
          <div className="grid gap-6 sm:grid-cols-2">
            {data.data.map((person) => (
              <Link
                key={person.id}
                to={`/person/${person.id}`}
                className="rounded-[2rem] border border-[#1E2A45] bg-[#131A2E]/80 p-6 transition hover:border-amber-400/50"
              >
                <p className="text-sm uppercase tracking-[0.24em] text-amber-300/80">{person.party}</p>
                <h2 className="mt-3 text-2xl font-semibold text-white">{person.name}</h2>
                <p className="mt-2 text-sm text-slate-400">{person.constituency}</p>
                <p className="mt-4 text-sm text-slate-400">Speeches: {person.speech_count}</p>
              </Link>
            ))}
          </div>
        ) : (
          <div className="rounded-[2rem] border border-[#1E2A45] bg-[#131A2E]/80 p-10 text-slate-300">
            No MPs matched "{query}". Try a broader keyword.
          </div>
        )}
      </section>
    </main>
  );
}
