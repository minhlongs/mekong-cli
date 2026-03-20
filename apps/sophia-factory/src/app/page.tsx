'use client'

import Link from 'next/link'
import { ArrowRight, Zap, Target, Sparkles, CheckCircle } from 'lucide-react'

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white">
      {/* Navigation */}
      <nav className="border-b bg-white/80 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-2">
              <Zap className="h-6 w-6 text-purple-600" />
              <span className="font-bold text-xl">Sophia AI Factory</span>
            </div>
            <div className="flex gap-4">
              <Link href="/auth/login" className="px-4 py-2 text-gray-600 hover:text-gray-900">
                Sign In
              </Link>
              <Link
                href="/auth/signup"
                className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition"
              >
                Get Started
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24">
        <div className="text-center">
          <h1 className="text-5xl md:text-6xl font-bold mb-6 bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
            Generate Winning Proposals
            <br />
            in Minutes, Not Days
          </h1>
          <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
            AI-powered proposal generator trained on your brand voice. Close more deals
            with proposals that sound exactly like you.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              href="/auth/signup"
              className="px-8 py-4 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition flex items-center justify-center gap-2 text-lg font-medium"
            >
              Start Free Trial
              <ArrowRight className="h-5 w-5" />
            </Link>
            <Link
              href="/dashboard"
              className="px-8 py-4 border border-gray-300 rounded-lg hover:bg-gray-50 transition text-lg font-medium"
            >
              View Demo
            </Link>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="bg-gray-50 py-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold mb-4">Everything You Need to Win More Deals</h2>
            <p className="text-gray-600 max-w-2xl mx-auto">
              Our AI learns your brand voice and generates proposals that convert prospects into clients.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <FeatureCard
              icon={<Target className="h-8 w-8 text-purple-600" />}
              title="Brand Voice Training"
              description="Upload your past proposals, docs, and content. Our AI learns your unique voice and style."
            />
            <FeatureCard
              icon={<Sparkles className="h-8 w-8 text-purple-600" />}
              title="AI-Powered Generation"
              description="Generate complete proposals in seconds. Just input client details and watch the magic happen."
            />
            <FeatureCard
              icon={<CheckCircle className="h-8 w-8 text-purple-600" />}
              title="Proven Results"
              description="Agencies using Sophia see 3x faster proposal creation and 40% higher win rates."
            />
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl font-bold mb-4">Ready to Transform Your Proposal Process?</h2>
          <p className="text-gray-600 mb-8">
            Join hundreds of agencies closing more deals with Sophia AI Factory.
          </p>
          <Link
            href="/auth/signup"
            className="inline-flex px-8 py-4 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition text-lg font-medium"
          >
            Start Your Free Trial
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t py-12 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center text-gray-600">
          <p>&copy; 2026 Sophia AI Factory. All rights reserved.</p>
        </div>
      </footer>
    </div>
  )
}

function FeatureCard({ icon, title, description }: { icon: React.ReactNode; title: string; description: string }) {
  return (
    <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 hover:shadow-md transition">
      <div className="mb-4">{icon}</div>
      <h3 className="text-xl font-semibold mb-2">{title}</h3>
      <p className="text-gray-600">{description}</p>
    </div>
  )
}
