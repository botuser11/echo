import React from 'react';
import { motion } from 'framer-motion';

const insights = [
  {
    title: 'Search the chamber',
    detail: 'Query speeches, claims, and MP positions across parliamentary debate history.',
  },
  {
    title: 'Claim timelines',
    detail: 'See how rhetoric changes over time and who shifts their position first.',
  },
  {
    title: 'Contradiction alerts',
    detail: 'Spot inconsistent statements with clear evidence and source references.',
  },
];

export default function Insights() {
  return (
    <main className="mx-auto flex w-full max-w-6xl flex-col gap-12 px-6 pb-16 pt-12 text-slate-100 sm:px-8">
      <motion.section
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.7 }}
        className="rounded-[2rem] border border-slate-800/90 bg-slate-950/75 p-10 shadow-glow"
      >
        <div className="space-y-4">
          <p className="text-sm uppercase tracking-[0.24em] text-amber-300/90">Insights</p>
          <h1 className="text-4xl font-semibold text-white sm:text-5xl">Investigate claims and debate trends with clarity.</h1>
          <p className="max-w-3xl text-lg leading-8 text-slate-400">
            Echo helps you surface the strongest evidence from UK parliamentary records, connect speakers to positions, and compare claims across parties.
          </p>
        </div>
      </motion.section>

      <section className="grid gap-6 lg:grid-cols-3">
        {insights.map((item) => (
          <motion.article
            key={item.title}
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, amount: 0.3 }}
            transition={{ duration: 0.55 }}
            className="rounded-[2rem] border border-slate-800/90 bg-slate-950/80 p-8"
          >
            <h2 className="text-2xl font-semibold text-white">{item.title}</h2>
            <p className="mt-4 text-slate-400">{item.detail}</p>
          </motion.article>
        ))}
      </section>

      <section className="rounded-[2rem] border border-slate-800/90 bg-slate-900/80 p-10 shadow-glow">
        <div className="space-y-4">
          <p className="text-sm uppercase tracking-[0.24em] text-amber-300/90">How it works</p>
          <p className="text-2xl font-semibold text-white">Built to keep your analysis grounded in source material.</p>
          <p className="max-w-3xl text-slate-400">
            Each insight in Echo is generated from the same transcripts and citations that shape parliamentary reporting. The platform is designed to support evidence-led reporting and rapid verification.
          </p>
        </div>
      </section>
    </main>
  );
}
