'use client'
import { motion } from 'framer-motion'

interface SectionHeadingProps {
  tag?: string
  title: string
  subtitle?: string
  align?: 'left' | 'center'
}

export default function SectionHeading({ tag, title, subtitle, align = 'center' }: SectionHeadingProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-80px' }}
      transition={{ duration: 0.7, ease: [0.25, 0.46, 0.45, 0.94] }}
      className={`mb-20 ${align === 'center' ? 'text-center' : 'text-left'}`}
    >
      {tag && (
        <span className="ds-badge-accent mb-5 inline-flex">{tag}</span>
      )}
      <h2 className="text-h2 lg:text-h1 text-ds-text">{title}</h2>
      {subtitle && (
        <p className="text-body-lg text-ds-text-secondary max-w-2xl mx-auto mt-5 leading-relaxed">{subtitle}</p>
      )}
    </motion.div>
  )
          }
