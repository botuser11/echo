import React from 'react';
import { motion } from 'framer-motion';

export default function About() {
  return (
    <main className="mx-auto flex w-full max-w-6xl flex-col gap-10 px-6 pb-16 pt-10 text-slate-100 sm:px-8">
      <motion.section
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.7 }}
        className="rounded-[2rem] border border-[#1E2A45] bg-[#131A2E]/80 p-10 shadow-glow"
      >
        <p className="text-sm uppercase tracking-[0.24em] text-amber-300/80">About Echo</p>
        <h1 className="mt-4 text-4xl font-semibold text-white">A public face for UK position intelligence.</h1>
        <p className="mt-4 max-w-3xl text-slate-400">
          Echo links speeches, claims, and politician profiles with verified evidence from Hansard and parliamentary records. It was designed for journalists, civic teams, and analysts who need source-backed insight into how public figures behave over time.
        </p>
      </motion.section>

      <section className="grid gap-6 lg:grid-cols-2">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.1 }}
          className="rounded-[2rem] border border-[#1E2A45] bg-[#131A2E]/80 p-8"
        >
          <h2 className="text-3xl font-semibold text-white">Source-backed insights</h2>
          <p className="mt-4 text-slate-400">
            Every claim and profile in Echo is grounded in parliamentary transcripts, so you can trust the evidence behind every summary.
          </p>
        </motion.div>
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.2 }}
          className="rounded-[2rem] border border-[#1E2A45] bg-[#131A2E]/80 p-8"
        >
          <h2 className="text-3xl font-semibold text-white">Designed for clarity</h2>
          <p className="mt-4 text-slate-400">
            Echo surfaces the most relevant MPs, speeches, and positions with a clean, dark interface built for quick analysis and rapid reporting.
          </p>
        </motion.div>
      </section>
    </main>
  );
}
