import React, { useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useQuery } from '@tanstack/react-query';
import { fetcher } from '../api/client';

interface PersonDetail {
  id: string;
  name: string;
  party: string;
  constituency: string;
  house: string;
  role?: string | null;
  photo_url?: string | null;
  speech_count: number;
  latest_speech_date?: string | null;
  contradiction_count: number;
  topic_positions: Array<{ id: string; name: string; slug: string; claim_count: number }>;
}

interface SpeechSummary {
  id: string;
  date: string;
  debate_title: string;
  full_text: string;
  source_url?: string | null;
}

interface SpeechListResponse {
  data: SpeechSummary[];
  meta: {
    total: number;
    page: number;
    page_size: number;
  };
}

const tabs = ['Speeches', 'Claims', 'Contradictions', 'Timeline'] as const;
type TabName = (typeof tabs)[number];

export default function Person() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<TabName>('Speeches');
  const [page, setPage] = useState(1);
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());

  const { data: person, error: personError, isLoading: isPersonLoading } = useQuery<PersonDetail, Error>({
    queryKey: ['person', id],
    queryFn: () => fetcher(`/api/persons/${id}`),
    enabled: Boolean(id),
    staleTime: 60000,
    retry: false,
  });

  const {
    data: speechData,
    error: speechError,
    isLoading: isSpeechLoading,
  } = useQuery<SpeechListResponse, Error>({
    queryKey: ['person-speeches', id, page],
    queryFn: () => fetcher(`/api/persons/${id}/speeches?page=${page}&page_size=20`),
    enabled: Boolean(id) && activeTab === 'Speeches',
    staleTime: 60000,
    retry: false,
  });

  const latestSpeechDate = person?.latest_speech_date
    ? new Date(person.latest_speech_date).toLocaleDateString('en-GB', {
        day: 'numeric',
        month: 'short',
        year: 'numeric',
      })
    : 'N/A';

  const speechList = speechData?.data ?? [];
  const totalPages = Math.max(1, Math.ceil((speechData?.meta.total ?? 0) / 20));

  const handleExpand = (speechId: string) => {
    setExpandedIds((prev) => {
      const next = new Set(prev);
      if (next.has(speechId)) {
        next.delete(speechId);
      } else {
        next.add(speechId);
      }
      return next;
    });
  };

  const backLabel = person?.name ? `Back to ${person.name}` : 'Back';
  const partyDot = <span className="inline-block h-3 w-3 rounded-full bg-amber-400" />;

  return (
    <main className="mx-auto flex w-full max-w-7xl flex-col gap-10 px-6 pb-16 pt-10 text-slate-100 sm:px-8">
      <section className="rounded-[2rem] border border-[#1E2A45] bg-[#131A2E]/80 p-8 shadow-glow">
        <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex items-center gap-4">
            <button
              type="button"
              onClick={() => navigate(-1)}
              className="rounded-full border border-[#1E2A45] bg-[#0D141F]/80 px-4 py-2 text-sm text-slate-200 transition hover:border-amber-400/50 hover:text-white"
            >
              Back
            </button>
            <div className="flex h-24 w-24 items-center justify-center overflow-hidden rounded-[1.75rem] border border-[#1E2A45] bg-[#0D141F]/80">
              {person?.photo_url ? (
                <img
                  src={person.photo_url}
                  alt={person?.name ?? 'MP photo'}
                  className="h-full w-full object-cover"
                />
              ) : (
                <span className="text-sm text-slate-400">No photo</span>
              )}
            </div>
          </div>

          <div className="space-y-4">
            <div className="flex flex-wrap items-center gap-3">
              <h1 className="text-4xl font-semibold text-white">{person?.name ?? 'MP profile'}</h1>
              <div className="flex items-center gap-2 text-sm text-slate-300">
                {partyDot}
                <span>{person?.party ?? 'Unknown party'}</span>
              </div>
            </div>
            <div className="space-y-2 text-slate-400">
              <p>{person?.role ?? person?.house ?? 'Role unavailable'}</p>
              <p>{person?.constituency ?? 'Constituency unavailable'}</p>
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="rounded-[1.75rem] border border-[#1E2A45] bg-[#0D141F]/80 p-5">
              <p className="text-sm text-slate-400">Total speeches</p>
              <p className="mt-3 text-3xl font-semibold text-white">{person?.speech_count ?? '-'}</p>
            </div>
            <div className="rounded-[1.75rem] border border-[#1E2A45] bg-[#0D141F]/80 p-5">
              <p className="text-sm text-slate-400">Latest speech</p>
              <p className="mt-3 text-3xl font-semibold text-white">{latestSpeechDate}</p>
            </div>
          </div>
        </div>
      </section>

      <section className="rounded-[2rem] border border-[#1E2A45] bg-[#131A2E]/80 p-6 shadow-glow">
        <div className="flex flex-wrap gap-2 border-b border-[#1E2A45]/50 pb-4">
          {tabs.map((tab) => (
            <button
              key={tab}
              type="button"
              onClick={() => setActiveTab(tab)}
              className={`rounded-full px-4 py-2 text-sm transition ${
                activeTab === tab
                  ? 'bg-amber-400 text-slate-950'
                  : 'text-slate-300 hover:bg-slate-900/80 hover:text-white'
              }`}
            >
              {tab}
            </button>
          ))}
        </div>

        {activeTab !== 'Speeches' ? (
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="mt-10 rounded-[2rem] border border-[#1E2A45] bg-[#0D141F]/80 p-10 text-center text-slate-300"
          >
            <p className="text-xl font-semibold text-white">Coming soon — AI analysis in progress</p>
            <p className="mt-3 max-w-2xl mx-auto text-sm leading-7 text-slate-400">
              This section is being prepared to surface claims, contradictions, and timeline signals as structured insights.
            </p>
          </motion.div>
        ) : (
          <div className="mt-8 space-y-6">
            {isSpeechLoading ? (
              <div className="space-y-4">
                {[...Array(3)].map((_, index) => (
                  <div key={index} className="animate-pulse rounded-[2rem] border border-[#1E2A45] bg-[#0D141F]/80 p-8" />
                ))}
              </div>
            ) : speechError ? (
              <div className="rounded-[2rem] border border-[#1E2A45] bg-[#0D141F]/80 p-10 text-slate-300">
                Unable to load speeches. Please refresh or try again.
              </div>
            ) : speechList.length === 0 ? (
              <div className="rounded-[2rem] border border-[#1E2A45] bg-[#0D141F]/80 p-10 text-slate-300">
                No speeches found for this MP.
              </div>
            ) : (
              <motion.div
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6 }}
                className="space-y-6"
              >
                {speechList.map((speech) => {
                  const expanded = expandedIds.has(speech.id);
                  const truncated = speech.full_text.length > 300 ? speech.full_text.slice(0, 300) + '...' : speech.full_text;

                  return (
                    <article
                      key={speech.id}
                      className="overflow-hidden rounded-[2rem] border-l-4 border-amber-400 bg-[#131A2E]/90 p-6 shadow-[0_20px_60px_rgba(15,23,42,0.2)]"
                    >
                      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                        <div>
                          <p className="text-sm uppercase tracking-[0.24em] text-amber-300/80">{new Date(speech.date).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })}</p>
                          <h3 className="mt-2 text-2xl font-semibold text-white">{speech.debate_title}</h3>
                        </div>
                        {speech.source_url ? (
                          <a
                            href={speech.source_url}
                            target="_blank"
                            rel="noreferrer"
                            className="rounded-full border border-[#1E2A45] bg-[#0D141F]/80 px-4 py-2 text-sm text-amber-300 transition hover:border-amber-400/50 hover:text-white"
                          >
                            View Hansard
                          </a>
                        ) : null}
                      </div>
                      <p className="mt-5 whitespace-pre-wrap text-slate-300">
                        {expanded ? speech.full_text : truncated}
                      </p>
                      {speech.full_text.length > 300 ? (
                        <button
                          type="button"
                          onClick={() => handleExpand(speech.id)}
                          className="mt-4 text-sm font-semibold text-amber-300 transition hover:text-amber-200"
                        >
                          {expanded ? 'Show less' : 'Read more'}
                        </button>
                      ) : null}
                    </article>
                  );
                })}

                <div className="flex flex-wrap items-center justify-between gap-4 rounded-[2rem] border border-[#1E2A45] bg-[#0D141F]/80 p-5">
                  <p className="text-sm text-slate-400">Page {page} of {totalPages}</p>
                  <div className="flex gap-3">
                    <button
                      type="button"
                      disabled={page <= 1}
                      onClick={() => setPage((current) => Math.max(1, current - 1))}
                      className="rounded-full border border-[#1E2A45] bg-[#131A2E]/80 px-4 py-2 text-sm text-slate-200 transition hover:border-amber-400/50 disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      Previous
                    </button>
                    <button
                      type="button"
                      disabled={page >= totalPages}
                      onClick={() => setPage((current) => Math.min(totalPages, current + 1))}
                      className="rounded-full border border-[#1E2A45] bg-[#131A2E]/80 px-4 py-2 text-sm text-slate-200 transition hover:border-amber-400/50 disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      Next
                    </button>
                  </div>
                </div>
              </motion.div>
            )}
          </div>
        )}
      </section>
    </main>
  );
}
