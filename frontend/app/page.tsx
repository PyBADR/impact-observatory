'use client';

import Link from 'next/link';
import { motion } from 'framer-motion';
import {
  Play,
  ArrowRight,
  MessageSquare,
  Radio,
  TrendingUp,
  AlertTriangle,
  Shield,
  Network,
  Layers,
  GitBranch,
  Users,
  BarChart3,
  Cpu,
  Terminal,
  Activity,
} from 'lucide-react';
import Navbar from '@/components/ui/Navbar';
import Footer from '@/components/ui/Footer';
import SectionHeading from '@/components/ui/SectionHeading';

export default function HomePage() {
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: { staggerChildren: 0.1, delayChildren: 0.2 },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
      opacity: 1,
      y: 0,
      transition: { duration: 0.7, ease: [0.25, 0.46, 0.45, 0.94] },
    },
  };

  return (
    <div className="min-h-screen bg-ds-bg text-ds-text">
      <Navbar />

      {/* HERO */}
      <section
        id="hero"
        className="relative min-h-screen flex items-center justify-center pt-20 overflow-hidden"
      >
        <div className="absolute inset-0 ds-grid-bg opacity-60" />
        <div className="absolute w-[600px] h-[600px] -top-20 -left-40 rounded-full bg-ds-accent/8 blur-[160px] pointer-events-none" />
        <div className="absolute w-[500px] h-[500px] bottom-0 right-0 rounded-full bg-purple-600/5 blur-[140px] pointer-events-none" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,transparent_0%,#06060A_75%)]" />

        <motion.div
          className="relative z-10 ds-container max-w-5xl mx-auto px-6 text-center"
          variants={containerVariants}
          initial="hidden"
          animate="visible"
        >
          <motion.div variants={itemVariants}>
            <div className="ds-badge-accent inline-flex items-center gap-2 mb-8">
              <Terminal className="w-3.5 h-3.5" />
              <span>Simulation Intelligence Engine</span>
            </div>
          </motion.div>

          <motion.h1
            variants={itemVariants}
            className="text-display-sm lg:text-display font-bold leading-[1.02] tracking-tight mb-8"
          >
            Simulate What
            <br />
            <span className="text-ds-accent">Happens Next</span>
          </motion.h1>

          <motion.p
            variants={itemVariants}
            className="text-body-lg text-ds-text-secondary max-w-2xl mx-auto mb-12 leading-relaxed"
          >
            Turn real-world inputs into entity graphs, agent behavior, and
            predictive simulation across GCC scenarios. See the future before it
            unfolds.
          </motion.p>

          <motion.div
            variants={itemVariants}
            className="flex flex-col sm:flex-row gap-4 justify-center"
          >
            <Link href="/demo" className="ds-btn-primary text-[15px] px-8 py-4">
              Enter the System
              <ArrowRight className="w-4 h-4" />
            </Link>
            <Link href="/architecture" className="ds-btn-secondary text-[15px] px-8 py-4">
              View Architecture
            </Link>
          </motion.div>

          <motion.div
            variants={itemVariants}
            className="mt-20 flex items-center justify-center gap-4 text-ds-text-dim"
          >
            <div className="flex items-center gap-2">
              <div className="w-1.5 h-1.5 rounded-full bg-ds-success animate-pulse" />
              <span className="text-nano font-mono uppercase tracking-wider">System Online</span>
            </div>
            <span className="text-nano">·</span>
            <span className="text-nano font-mono uppercase tracking-wider">6 Agent Archetypes</span>
            <span className="text-nano">·</span>
            <span className="text-nano font-mono uppercase tracking-wider">GCC Ready</span>
          </motion.div>
        </motion.div>
      </section>

      {/* WATCH IN ACTION */}
      <section className="ds-section">
        <div className="ds-container">
          <SectionHeading tag="Demo" title="Watch Deevo Sim in Action" />
          <motion.div
            className="grid grid-cols-1 lg:grid-cols-5 gap-6"
            initial={{ opacity: 0, y: 24 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '-60px' }}
            transition={{ duration: 0.7 }}
          >
            <div className="lg:col-span-2 flex flex-col gap-5">
              {[
                { num: '01', title: 'Fuel Price Increase in Saudi Arabia', desc: 'Simulating public reaction to a 10% fuel price hike and its spread across social media in the Kingdom.' },
                { num: '02', title: 'Kuwait Hashtag Reaction', desc: 'Tracking how a viral hashtag spreads through influencer networks following an economic policy announcement.' },
              ].map((item) => (
                <div key={item.num} className="ds-card-interactive p-7 group">
                  <div className="text-nano font-mono text-ds-accent bg-ds-accent-muted px-2.5 py-1 rounded-md inline-block">{item.num}</div>
                  <h3 className="text-h4 mt-5 group-hover:text-ds-text transition-colors">{item.title}</h3>
                  <p className="text-caption text-ds-text-secondary mt-3 leading-relaxed">{item.desc}</p>
                </div>
              ))}
            </div>
            <div className="lg:col-span-3">
              <div className="ds-gradient-border p-[1px] h-full">
                <div className="bg-ds-surface rounded-ds-xl h-full min-h-[360px] flex flex-col items-center justify-center relative overflow-hidden">
                  <div className="absolute inset-0 ds-grid-bg opacity-30" />
                  <div className="relative z-10 flex flex-col items-center">
                    <div className="w-18 h-18 rounded-full bg-ds-accent/10 border border-ds-accent/25 flex items-center justify-center cursor-pointer hover:bg-ds-accent/18 hover:border-ds-accent/40 transition-all duration-300 hover:shadow-ds-glow-accent">
                      <Play className="w-7 h-7 text-ds-accent ml-0.5" />
                    </div>
                    <p className="text-caption text-ds-text-secondary mt-5">See the full simulation pipeline</p>
                  </div>
                  <div className="absolute bottom-5 right-5 flex items-center gap-2 text-nano font-mono bg-ds-bg/80 backdrop-blur-sm px-3 py-1.5 rounded-ds border border-ds-border/50">
                    <Activity className="w-3 h-3 text-ds-accent" />
                    2:34
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* 5-STEP PROCESS */}
      <section className="ds-section bg-ds-bg-alt">
        <div className="ds-container">
          <SectionHeading
            tag="Pipeline"
            title="Simulate in 5 Steps"
            subtitle="From raw scenario input to explainable prediction — built as a layered intelligence pipeline."
          />
          <motion.div
            className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-5"
            initial={{ opacity: 0, y: 24 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '-60px' }}
            transition={{ duration: 0.7 }}
          >
            {[
              { icon: Layers, step: '01', title: 'Input Scenario', desc: 'Provide a real-world scenario in Arabic or English — policy changes, market events, social triggers.' },
              { icon: Cpu, step: '02', title: 'Extract Entities', desc: 'Identify people, organizations, topics, regions, and platforms from the input.' },
              { icon: GitBranch, step: '03', title: 'Build Graph', desc: 'Map relationships — influence, reaction, amplification, regulation — into a directed graph.' },
              { icon: Users, step: '04', title: 'Run Agents', desc: 'Deploy GCC-specific personas with behavioral profiles to simulate reactions over time.' },
              { icon: BarChart3, step: '05', title: 'Generate Report', desc: 'Produce prediction summaries, confidence scores, spread analysis, and key drivers.' },
            ].map((item, idx) => {
              const IconComponent = item.icon;
              return (
                <motion.div
                  key={idx}
                  className="ds-card p-7 flex flex-col group hover:border-ds-accent/15 transition-all duration-300"
                  initial={{ opacity: 0, y: 16 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: idx * 0.08, duration: 0.6 }}
                >
                  <div className="w-10 h-10 rounded-ds bg-ds-surface-raised border border-ds-border flex items-center justify-center mb-5 group-hover:border-ds-accent/20 transition-colors">
                    <IconComponent className="w-[18px] h-[18px] text-ds-text-muted group-hover:text-ds-accent transition-colors" />
                  </div>
                  <div className="text-nano font-mono text-ds-accent-dim">{item.step}</div>
                  <h3 className="text-h4 mt-2 text-left">{item.title}</h3>
                  <p className="text-caption text-ds-text-secondary mt-2.5 flex-grow text-left leading-relaxed">{item.desc}</p>
                </motion.div>
              );
            })}
          </motion.div>
        </div>
      </section>

      {/* USE CASES */}
      <section className="ds-section">
        <div className="ds-container">
          <SectionHeading tag="Use Cases" title="Built for GCC Scenarios" />
          <motion.div
            className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5"
            initial={{ opacity: 0, y: 24 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '-60px' }}
            transition={{ duration: 0.7 }}
          >
            {[
              { icon: MessageSquare, title: 'Public Reaction', desc: 'Model citizen response to policy changes and government announcements across Gulf demographics.' },
              { icon: Radio, title: 'Media Spread', desc: 'Track how news amplifies through media networks, influencer chains, and social platforms.' },
              { icon: TrendingUp, title: 'Economic Response', desc: 'Simulate market and public sentiment shifts following economic events and pricing reforms.' },
              { icon: AlertTriangle, title: 'Brand Backlash', desc: 'Predict and rehearse corporate response scenarios for brand-threatening events.' },
              { icon: Shield, title: 'Policy Perception', desc: 'Understand how government policies are received across different demographic segments.' },
              { icon: Network, title: 'Signal Mapping', desc: 'Map influence pathways and signal propagation across connected audience networks.' },
            ].map((item, idx) => {
              const IconComponent = item.icon;
              return (
                <motion.div
                  key={idx}
                  className="ds-card-interactive p-7"
                  initial={{ opacity: 0, y: 16 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: idx * 0.06, duration: 0.6 }}
                >
                  <div className="w-11 h-11 rounded-ds bg-ds-accent-muted flex items-center justify-center">
                    <IconComponent className="w-5 h-5 text-ds-accent" />
                  </div>
                  <h3 className="text-h4 mt-5">{item.title}</h3>
                  <p className="text-caption text-ds-text-secondary mt-2.5 leading-relaxed">{item.desc}</p>
                </motion.div>
              );
            })}
          </motion.div>
        </div>
      </section>

      {/* ABOUT */}
      <section id="about" className="ds-section bg-ds-bg-alt">
        <div className="ds-container">
          <SectionHeading tag="About" title="Built to Rehearse Reality" />
          <motion.div
            className="max-w-3xl mx-auto"
            initial={{ opacity: 0, y: 24 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '-60px' }}
            transition={{ duration: 0.7 }}
          >
            <p className="text-body-lg text-ds-text-secondary leading-relaxed text-center">
              Deevo Sim creates a digital simulation layer from real-world scenarios, helping teams
              understand how reactions may spread, evolve, and intensify across connected audiences.
              Built with GCC context at its core, the platform combines entity extraction,
              relationship mapping, agent-based modeling, and predictive analytics into a single
              intelligence pipeline.
            </p>
            <div className="mt-16 grid grid-cols-1 sm:grid-cols-3 gap-6">
              {[
                { value: '6', label: 'Agent Archetypes' },
                { value: '4', label: 'Simulation Steps' },
                { value: '84%', label: 'Confidence Score' },
              ].map((stat, idx) => (
                <motion.div
                  key={idx}
                  className="ds-card p-6 text-center"
                  initial={{ opacity: 0, y: 12 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: idx * 0.1, duration: 0.5 }}
                >
                  <div className="text-h1 text-ds-accent font-mono font-bold">{stat.value}</div>
                  <div className="text-micro text-ds-text-muted mt-2 uppercase tracking-wider">{stat.label}</div>
                </motion.div>
              ))}
            </div>
          </motion.div>
        </div>
      </section>

      {/* CTA */}
      <section className="ds-section">
        <div className="ds-container">
          <motion.div
            className="ds-gradient-border p-[1px] max-w-3xl mx-auto"
            initial={{ opacity: 0, y: 24 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '-60px' }}
            transition={{ duration: 0.7 }}
          >
            <div className="ds-card p-14 lg:p-20 rounded-ds-xl text-center bg-gradient-to-br from-ds-surface to-ds-bg">
              <h2 className="text-h2 lg:text-h1 text-ds-text">Enter the Simulation</h2>
              <p className="text-body-lg text-ds-text-secondary mt-4 max-w-xl mx-auto">
                Experience the full pipeline — from scenario input to predictive intelligence.
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center mt-10">
                <Link href="/demo" className="ds-btn-primary text-[15px] px-8 py-4">
                  Launch System
                  <ArrowRight className="w-4 h-4" />
                </Link>
                <Link href="/architecture" className="ds-btn-secondary text-[15px] px-8 py-4">
                  Explore Architecture
                </Link>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      <Footer />
    </div>
  );
}
