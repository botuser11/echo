import React from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { Link, Route, Routes, useLocation } from 'react-router-dom';
import About from './pages/About';
import Home from './pages/Home';
import Person from './pages/Person';
import Search from './pages/Search';

function App() {
  const location = useLocation();

  return (
    <div className="min-h-screen bg-[#0A0F1C] text-slate-100">
      <div className="mx-auto max-w-7xl px-6 py-6 sm:px-8">
        <header className="rounded-[2rem] border border-[#1E2A45] bg-[#131A2E]/90 p-6 shadow-glow sm:flex sm:items-center sm:justify-between">
          <div className="space-y-1">
            <p className="text-sm uppercase tracking-[0.3em] text-amber-300/80">Echo</p>
            <p className="text-2xl font-semibold text-white sm:text-3xl">What did they actually say?</p>
          </div>

          <nav className="mt-4 flex flex-wrap gap-3 text-sm sm:mt-0">
            <Link
              to="/"
              className="rounded-full px-4 py-2 text-slate-200 transition hover:bg-slate-900/80 hover:text-white"
            >
              Home
            </Link>
            <Link
              to="/search"
              className="rounded-full px-4 py-2 text-slate-200 transition hover:bg-slate-900/80 hover:text-white"
            >
              Search
            </Link>
            <Link
              to="/about"
              className="rounded-full px-4 py-2 text-slate-200 transition hover:bg-slate-900/80 hover:text-white"
            >
              About
            </Link>
          </nav>
        </header>
      </div>

      <AnimatePresence mode="wait">
        <motion.div
          key={location.pathname}
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -18 }}
          transition={{ duration: 0.45, ease: 'easeOut' }}
        >
          <Routes location={location} key={location.pathname}>
            <Route path="/" element={<Home />} />
            <Route path="/search" element={<Search />} />
            <Route path="/person/:id" element={<Person />} />
            <Route path="/about" element={<About />} />
          </Routes>
        </motion.div>
      </AnimatePresence>

      <footer className="mx-auto max-w-7xl px-6 pb-10 pt-8 sm:px-8">
        <div className="rounded-[2rem] border border-[#1E2A45] bg-[#131A2E]/80 p-6 text-center text-slate-500">
          Built by Karthik Shanmuganathan Valluvar
        </div>
      </footer>
    </div>
  );
}

export default App;
