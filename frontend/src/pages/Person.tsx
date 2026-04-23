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

interface ClaimData {
  id: string;
  claim_text: string;
  original_quote?: string | null;
  topic?: string | null;
  stance: string;
  confidence: number;
  date: string;
  source_url?: string | null;
}

interface PaginatedClaimResponse {
  data: ClaimData[];
  meta: {
    total: number;
    page: number;
    page_size: number;
  };
}

interface ContradictionClaimData {
  id: string;
  date: string;
  claim_text: string;
  original_quote?: string | null;
  topic?: string | null;
  stance: string;
}

interface ContradictionItem {
  id: string;
  claim_a: ContradictionClaimData;
  claim_b: ContradictionClaimData;
  explanation: string;
  severity: string;
  status: string;
  detected_at: string;
}

const tabs = ['Speeches', 'Claims', 'Contradictions', 'Timeline'] as const;
type TabName = (typeof tabs)[number];

// Strip HTML tags from text
const stripHtml = (html: string): string => {
  return html.replace(/<[^>]*>/g, '');
};

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

  const {
    data: claimData,
    error: claimError,
    isLoading: isClaimLoading,
  } = useQuery<PaginatedClaimResponse, Error>({
    queryKey: ['person-claims', id, page],
    queryFn: () => fetcher(`/api/persons/${id}/claims?page=${page}&page_size=20`),
    enabled: Boolean(id) && activeTab === 'Claims',
    staleTime: 60000,
    retry: false,
  });

  const {
    data: contradictionData,
    error: contradictionError,
    isLoading: isContradictionLoading,
  } = useQuery<ContradictionItem[], Error>({
    queryKey: ['person-contradictions', id],
    queryFn: () => fetcher(`/api/persons/${id}/contradictions`),
    enabled: Boolean(id) && activeTab === 'Contradictions',
    staleTime: 60000,
    retry: false,
  });

  const {
    data: rawTimelineData,
    error: timelineError,
    isLoading: isTimelineLoading,
  } = useQuery<ClaimData[], Error>({
    queryKey: ['person-timeline', id],
    queryFn: async () => {
      const firstPage = await fetcher<PaginatedClaimResponse>(`/api/persons/${id}/claims?page=1&page_size=100`);
      const total = firstPage.meta.total;
      if (total <= 100) {
        return firstPage.data;
      }

      const totalPages = Math.ceil(total / 100);
      const extraPages = await Promise.all(
        Array.from({ length: totalPages - 1 }, (_, index) =>
          fetcher<PaginatedClaimResponse>(`/api/persons/${id}/claims?page=${index + 2}&page_size=100`)
        )
      );

      return [firstPage.data, ...extraPages.map((pageData) => pageData.data)].flat();
    },
    enabled: Boolean(id) && activeTab === 'Timeline',
    staleTime: 60000,
    retry: false,
  });

  const totalClaims = claimData?.meta.total ?? 0;
  const totalClaimPages = Math.max(1, Math.ceil(totalClaims / 20));

  const latestSpeechDate = person?.latest_speech_date
    ? new Date(person.latest_speech_date).toLocaleDateString('en-GB', {
        day: 'numeric',
        month: 'short',
        year: 'numeric',
      })
    : 'N/A';

  const speechList = speechData?.data ?? [];
  const totalPages = Math.max(1, Math.ceil((speechData?.meta.total ?? 0) / 20));

  const timelineClaims = useMemo(() => {
    if (!rawTimelineData) return [];
    return [...rawTimelineData].sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
  }, [rawTimelineData]);

  const timelineGroups = useMemo(() => {
    const groups = new Map<string, { label: string; items: ClaimData[] }>();
    timelineClaims.forEach((claim) => {
      const date = new Date(claim.date);
      const monthKey = `${date.getFullYear()}-${date.getMonth()}`;
      const label = date.toLocaleDateString('en-GB', { month: 'long', year: 'numeric' });
      if (!groups.has(monthKey)) {
        groups.set(monthKey, { label, items: [] });
      }
      groups.get(monthKey)?.items.push(claim);
    });
    return Array.from(groups.values());
  }, [timelineClaims]);

  const formatDate = (dateString: string): string =>
    new Date(dateString).toLocaleDateString('en-GB', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
    });

  const stripHtml = (html: string): string => {
    return html.replace(/<[^>]*>/g, '');
  };

  const getTopicBadgeClass = (topic?: string) =>
    topic
      ? 'rounded-full border border-amber-400/20 bg-amber-400/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-amber-200'
      : 'rounded-full border border-slate-700 bg-slate-900/90 px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-slate-400';

  const getSeverityClass = (severity: string) =>
    severity === 'high' ? 'bg-red-500' : 'bg-amber-400';

  const handleTabClick = (tab: TabName) => {
    setActiveTab(tab);
    if (tab === 'Speeches' || tab === 'Claims') {
      setPage(1);
    }
  };

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
              onClick={() => handleTabClick(tab)}
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

        {activeTab === 'Speeches' ? (
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
                  const cleanedText = stripHtml(speech.full_text);
                  const truncated = cleanedText.length > 200 ? cleanedText.slice(0, 200) + '...' : cleanedText;

                  return (
                    <article
                      key={speech.id}
                      className="overflow-hidden rounded-[2rem] border-l-4 border-amber-400 bg-[#131A2E]/90 p-6 shadow-[0_20px_60px_rgba(15,23,42,0.2)]"
                    >
                      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                        <div>
                          <p className="text-sm uppercase tracking-[0.24em] text-amber-300/80">{formatDate(speech.date)}</p>
                          <h3 className="mt-2 text-2xl font-semibold text-white">{speech.debate_title}</h3>
                        </div>
                        {speech.source_url ? (
                          <a
                            href={speech.source_url}
                            target="_blank"
                            rel="noreferrer"
                            className="rounded-full border border-[#1E2A45] bg-[#0D141F]/80 px-4 py-2 text-sm text-amber-300 transition hover:border-amber-400/50 hover:text-white"
                          >
                            View on Hansard ↗
                          </a>
                        ) : null}
                      </div>
                      <p className="mt-5 whitespace-pre-wrap text-slate-300">
                        {expanded ? cleanedText : truncated}
                      </p>
                      {cleanedText.length > 200 ? (
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
        ) : activeTab === 'Claims' ? (
          <div className="mt-8 space-y-6">
            <div className="flex flex-col gap-3 rounded-[2rem] border border-[#1E2A45] bg-[#0D141F]/80 p-6 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p className="text-sm uppercase tracking-[0.24em] text-amber-300/80">Claims</p>
                <h2 className="mt-2 text-3xl text-white" style={{ fontFamily: 'Instrument Serif, Georgia, serif' }}>Claim feed</h2>
                <p className="mt-2 text-sm text-slate-400">Showing {totalClaims} claims, newest first.</p>
              </div>
              <span className="rounded-full border border-amber-400/20 bg-amber-400/10 px-4 py-2 text-sm font-semibold text-amber-200">
                Updated daily
              </span>
            </div>

            {isClaimLoading ? (
              <div className="space-y-4">
                {[...Array(3)].map((_, index) => (
                  <div key={index} className="animate-pulse rounded-[2rem] border border-[#1E2A45] bg-[#0D141F]/80 p-8" />
                ))}
              </div>
            ) : claimError ? (
              <div className="rounded-[2rem] border border-[#1E2A45] bg-[#0D141F]/80 p-10 text-slate-300">
                Unable to load claims. Please refresh or try again.
              </div>
            ) : claimData?.data.length === 0 ? (
              <div className="rounded-[2rem] border border-[#1E2A45] bg-[#0D141F]/80 p-10 text-slate-300">
                No claims found for this MP.
              </div>
            ) : (
              <motion.div
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6 }}
                className="space-y-6"
              >
                {claimData.data.map((claim) => (
                  <article
                    key={claim.id}
                    className="overflow-hidden rounded-[2rem] border border-[#1E2A45] bg-[#131A2E]/90 p-6 shadow-[0_20px_60px_rgba(15,23,42,0.2)]"
                  >
                    <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                      <div className="space-y-3">
                        <div className="flex flex-wrap items-center gap-3">
                          <span className={getTopicBadgeClass(claim.topic)}>{claim.topic ?? 'No topic'}</span>
                          <span className="rounded-full border border-amber-400/20 bg-[#0D141F]/80 px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-amber-200">
                            {claim.stance}
                          </span>
                        </div>
                        <p className="text-sm uppercase tracking-[0.24em] text-amber-300/80">{formatDate(claim.date)}</p>
                        <p className="text-xl font-semibold text-white">{claim.claim_text}</p>
                      </div>
                      {claim.source_url ? (
                        <a
                          href={claim.source_url}
                          target="_blank"
                          rel="noreferrer"
                          className="rounded-full border border-[#1E2A45] bg-[#0D141F]/80 px-4 py-2 text-sm text-amber-300 transition hover:border-amber-400/50 hover:text-white"
                        >
                          Source ↗
                        </a>
                      ) : null}
                    </div>
                    {claim.original_quote ? (
                      <blockquote className="mt-5 rounded-[1.75rem] border border-[#1E2A45] bg-[#0D141F]/80 p-5 text-slate-300">
                        “{claim.original_quote}”
                      </blockquote>
                    ) : null}
                  </article>
                ))}

                <div className="flex flex-wrap items-center justify-between gap-4 rounded-[2rem] border border-[#1E2A45] bg-[#0D141F]/80 p-5">
                  <p className="text-sm text-slate-400">Page {page} of {totalClaimPages}</p>
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
                      disabled={page >= totalClaimPages}
                      onClick={() => setPage((current) => Math.min(totalClaimPages, current + 1))}
                      className="rounded-full border border-[#1E2A45] bg-[#131A2E]/80 px-4 py-2 text-sm text-slate-200 transition hover:border-amber-400/50 disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      Next
                    </button>
                  </div>
                </div>
              </motion.div>
            )}
          </div>
        ) : activeTab === 'Contradictions' ? (
          <div className="mt-8 space-y-6">
            <div className="rounded-[2rem] border border-[#1E2A45] bg-[#0D141F]/80 p-6">
              <p className="text-sm uppercase tracking-[0.24em] text-amber-300/80">Contradictions</p>
              <h2 className="mt-2 text-3xl text-white" style={{ fontFamily: 'Instrument Serif, Georgia, serif' }}>Viral contradiction dashboard</h2>
              <p className="mt-2 text-sm text-slate-400">See the most striking claim reversals, complete with evidence and severity.</p>
            </div>

            {isContradictionLoading ? (
              <div className="space-y-4">
                {[...Array(2)].map((_, index) => (
                  <div key={index} className="animate-pulse rounded-[2rem] border border-[#1E2A45] bg-[#0D141F]/80 p-10" />
                ))}
              </div>
            ) : contradictionError ? (
              <div className="rounded-[2rem] border border-[#1E2A45] bg-[#0D141F]/80 p-10 text-slate-300">
                Unable to load contradictions. Please refresh or try again.
              </div>
            ) : contradictionData?.length === 0 ? (
              <div className="rounded-[2rem] border border-[#1E2A45] bg-[#0D141F]/80 p-10 text-slate-300">
                No contradictions found for this MP.
              </div>
            ) : (
              <motion.div
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6 }}
                className="space-y-8"
              >
                {contradictionData.map((item) => (
                  <article
                    key={item.id}
                    className="overflow-hidden rounded-[2rem] border border-[#1E2A45] bg-[#131A2E]/90 p-6 shadow-[0_20px_60px_rgba(15,23,42,0.2)]"
                  >
                    <div className="grid gap-6 lg:grid-cols-[1.1fr_auto_1.1fr] lg:items-center">
                      <div className="space-y-4 rounded-[1.75rem] border border-[#1E2A45] bg-[#0D141F]/80 p-6">
                        <div className="flex items-center justify-between gap-3">
                          <span className="text-xs uppercase tracking-[0.22em] text-amber-300/80">Claim A</span>
                          <span className="rounded-full border border-amber-400/20 bg-[#0D141F]/80 px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-amber-200">
                            {item.claim_a.stance}
                          </span>
                        </div>
                        <div>
                          <p className="text-sm text-slate-400">{formatDate(item.claim_a.date)}</p>
                          <p className={getTopicBadgeClass(item.claim_a.topic)}>{item.claim_a.topic ?? 'No topic'}</p>
                        </div>
                        <p className="mt-4 text-lg font-semibold text-white">{item.claim_a.claim_text}</p>
                        {item.claim_a.original_quote ? (
                          <blockquote className="mt-4 rounded-[1.5rem] border border-[#1E2A45] bg-[#131A2E]/80 p-4 text-slate-300">
                            “{item.claim_a.original_quote}”
                          </blockquote>
                        ) : null}
                      </div>

                      <div className="mx-auto flex h-24 w-24 items-center justify-center rounded-full border border-amber-400/30 bg-[#0D141F]/90 text-2xl font-semibold text-amber-200">
                        vs
                      </div>

                      <div className="space-y-4 rounded-[1.75rem] border border-[#1E2A45] bg-[#0D141F]/80 p-6">
                        <div className="flex items-center justify-between gap-3">
                          <span className="text-xs uppercase tracking-[0.22em] text-amber-300/80">Claim B</span>
                          <span className="rounded-full border border-amber-400/20 bg-[#0D141F]/80 px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-amber-200">
                            {item.claim_b.stance}
                          </span>
                        </div>
                        <div>
                          <p className="text-sm text-slate-400">{formatDate(item.claim_b.date)}</p>
                          <p className={getTopicBadgeClass(item.claim_b.topic)}>{item.claim_b.topic ?? 'No topic'}</p>
                        </div>
                        <p className="mt-4 text-lg font-semibold text-white">{item.claim_b.claim_text}</p>
                        {item.claim_b.original_quote ? (
                          <blockquote className="mt-4 rounded-[1.5rem] border border-[#1E2A45] bg-[#131A2E]/80 p-4 text-slate-300">
                            “{item.claim_b.original_quote}”
                          </blockquote>
                        ) : null}
                      </div>
                    </div>

                    <div className="mt-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                      <div className="flex items-center gap-3">
                        <span className={`inline-block h-3 w-24 rounded-full ${getSeverityClass(item.severity)}`} />
                        <span className="text-sm uppercase tracking-[0.18em] text-slate-400">{item.severity}</span>
                      </div>
                      <p className="text-sm text-slate-500">Detected {formatDate(item.detected_at)}</p>
                    </div>

                    <div className="mt-4 rounded-[1.5rem] border border-[#1E2A45] bg-[#0D141F]/80 p-5">
                      <p className="text-sm uppercase tracking-[0.2em] text-amber-300/80">Explanation</p>
                      <p className="mt-3 text-slate-300">{item.explanation}</p>
                    </div>
                  </article>
                ))}
              </motion.div>
            )}
          </div>
        ) : (
          <div className="mt-8 space-y-8">
            <div className="rounded-[2rem] border border-[#1E2A45] bg-[#0D141F]/80 p-6">
              <p className="text-sm uppercase tracking-[0.24em] text-amber-300/80">Timeline</p>
              <h2 className="mt-2 text-3xl text-white" style={{ fontFamily: 'Instrument Serif, Georgia, serif' }}>Claim timeline</h2>
              <p className="mt-2 text-sm text-slate-400">Track position shifts and policy swings over time.</p>
            </div>

            {isTimelineLoading ? (
              <div className="space-y-4">
                {[...Array(3)].map((_, index) => (
                  <div key={index} className="animate-pulse rounded-[2rem] border border-[#1E2A45] bg-[#0D141F]/80 p-8" />
                ))}
              </div>
            ) : timelineError ? (
              <div className="rounded-[2rem] border border-[#1E2A45] bg-[#0D141F]/80 p-10 text-slate-300">
                Unable to load timeline. Please refresh or try again.
              </div>
            ) : timelineGroups.length === 0 ? (
              <div className="rounded-[2rem] border border-[#1E2A45] bg-[#0D141F]/80 p-10 text-slate-300">
                No timeline items available for this MP.
              </div>
            ) : (
              <motion.div
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6 }}
                className="space-y-10"
              >
                {timelineGroups.map((group) => (
                  <section key={group.label} className="space-y-6">
                    <h3 className="text-2xl font-semibold text-white" style={{ fontFamily: 'Instrument Serif, Georgia, serif' }}>
                      {group.label}
                    </h3>
                    <div className="relative overflow-hidden rounded-[2rem] border border-[#1E2A45] bg-[#0D141F]/80 p-6">
                      <div className="absolute left-6 top-10 h-[calc(100%-2.5rem)] w-px bg-slate-700" />
                      <div className="space-y-10 pl-12">
                        {group.items.map((claim) => (
                          <div key={claim.id} className="relative">
                            <span className="absolute left-0 top-3 block h-3 w-3 rounded-full bg-amber-400 ring-2 ring-[#0D141F]" />
                            <div className="rounded-[1.75rem] border border-[#1E2A45] bg-[#131A2E]/90 p-5">
                              <div className="flex flex-wrap items-center justify-between gap-3">
                                <span className={getTopicBadgeClass(claim.topic)}>{claim.topic ?? 'No topic'}</span>
                                <span className="rounded-full bg-[#0D141F]/80 px-3 py-1 text-xs uppercase tracking-[0.2em] text-slate-200">
                                  {claim.stance}
                                </span>
                              </div>
                              <p className="mt-4 text-sm uppercase tracking-[0.22em] text-amber-300/80">{formatDate(claim.date)}</p>
                              <p className="mt-2 text-lg font-semibold text-white">{claim.claim_text}</p>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </section>
                ))}
              </motion.div>
            )}
          </div>
        )}
      </section>
    </main>
  );
}
