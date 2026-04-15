import React from 'react';
import { motion } from 'framer-motion';

const features = [
  {
    title: 'Individual MP profiles',
    detail: 'Compare speeches, party affiliation, and public statements with timeline context.',
  },
  {
    title: 'Policy tagging',
    detail: 'Filter by issue area and discover how MPs respond to the same topic differently.',
  },
  {
    title: 'Historical comparison',
    detail: 'See whether claims are consistent across sessions, votes, and committees.',
  },
];

export default function Profiles() {
  return (
    <main className="mx-auto flex w-full max-w-6xl flex-col gap-12 px-6 pb-16 pt-12 text-slate-100 sm:px-8">
      <motion.section
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.7 }}
        className="rounded-[2rem] border border-slate-800/90 bg-slate-950/75 p-10 shadow-glow"
      >
        <div className="space-y-4">
          <p className="text-sm uppercase tracking-[0.24em] text-amber-300/90">Profiles</p>
          <h1 className="text-4xl font-semibold text-white sm:text-5xl">Access the people behind the positions.</h1>
          <p className="max-w-3xl text-lg leading-8 text-slate-400">
            Explore MP timelines, claim histories, and behavioural shifts across speeches so you can tell the story behind the data.
          </p>
        </div>
      </motion.section>

      <section className="grid gap-6 lg:grid-cols-3">
        {features.map((item) => (
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

      <section className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr] rounded-[2rem] border border-slate-800/90 bg-slate-900/80 p-10 shadow-glow">
        <div className="space-y-4">
          <p className="text-sm uppercase tracking-[0.24em] text-amber-300/90">Why profiles matter</p>
          <p className="text-2xl font-semibold text-white">Profiles bring context to claims and deliver more reliable narrative for your audience.</p>
          <p className="max-w-3xl text-slate-400">
            Use Echo to differentiate between repeated claims, one-off statements, and long-term policy behaviour.
          </p>
        </div>
        <div className="rounded-[2rem] bg-slate-950/80 p-8 text-slate-300">
          <p className="text-sm uppercase tracking-[0.24em] text-slate-500">Sample view</p>
          <div className="mt-6 space-y-3 border border-slate-800/80 rounded-3xl bg-slate-900/80 p-6">
            <p className="text-sm text-slate-400">Andrea Taylor · Labour</p>
            <p className="text-xl font-semibold text-white">Consistent support for green industry spending.</p>
            <p className="mt-3 text-slate-400">Claims matched across 18 speeches, with 4 flagged contradictions in related policy statements.</p>
          </div>
        </div>
      </section>
    </main>
  );
}
