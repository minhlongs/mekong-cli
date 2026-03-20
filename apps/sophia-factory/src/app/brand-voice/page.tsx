'use client'

import { useState } from 'react'
import { Upload, FileText, CheckCircle, Loader2, Zap, Trash2 } from 'lucide-react'
import { supabase, type BrandVoice } from '@/lib/supabase'

export default function BrandVoicePage() {
  const [brandVoice, setBrandVoice] = useState<BrandVoice | null>(null)
  const [uploading, setUploading] = useState(false)
  const [files, setFiles] = useState<File[]>([])
  const [trainingStatus, setTrainingStatus] = useState('not_started')

  async function handleFileUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const selectedFiles = e.target.files
    if (selectedFiles) {
      setFiles(prev => [...prev, ...Array.from(selectedFiles)])
    }
  }

  async function handleTrainModel() {
    setUploading(true)

    // TODO: Implement actual file upload and training
    // This is a placeholder for the training flow

    setTimeout(() => {
      setTrainingStatus('training')
      setUploading(false)
    }, 1000)
  }

  function removeFile(index: number) {
    setFiles(prev => prev.filter((_, i) => i !== index))
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-2">
              <Zap className="h-6 w-6 text-purple-600" />
              <span className="font-bold text-xl">Sophia AI Factory</span>
            </div>
            <div className="flex items-center gap-4">
              <a href="/dashboard" className="text-sm text-gray-600 hover:text-gray-900">
                Dashboard
              </a>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Brand Voice Trainer</h1>
          <p className="text-gray-600">
            Upload your content to train the AI on your unique brand voice and style.
          </p>
        </div>

        {/* Status Card */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 mb-8">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">Model Status</h2>
            <StatusBadge status={trainingStatus} />
          </div>

          <div className="space-y-3">
            <div className="flex items-center gap-3 text-sm">
              <CheckCircle className={`h-5 w-5 ${trainingStatus !== 'not_started' ? 'text-green-600' : 'text-gray-300'}`} />
              <span className={trainingStatus !== 'not_started' ? 'text-gray-900' : 'text-gray-500'}>
                Documents uploaded
              </span>
            </div>
            <div className="flex items-center gap-3 text-sm">
              <CheckCircle className={`h-5 w-5 ${trainingStatus === 'ready' ? 'text-green-600' : 'text-gray-300'}`} />
              <span className={trainingStatus === 'ready' ? 'text-gray-900' : 'text-gray-500'}>
                Model trained and ready
              </span>
            </div>
          </div>
        </div>

        {/* Upload Section */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 mb-8">
          <h2 className="text-lg font-semibold mb-4">Upload Training Documents</h2>

          <div
            className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-purple-400 transition cursor-pointer"
            onDragOver={(e) => e.preventDefault()}
            onDrop={(e) => {
              e.preventDefault()
              const droppedFiles = Array.from(e.dataTransfer.files)
              setFiles(prev => [...prev, ...droppedFiles])
            }}
          >
            <Upload className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600 mb-2">
              Drag and drop files here, or click to browse
            </p>
            <p className="text-sm text-gray-500">
              Support for PDF, DOCX, TXT, MD (max 10MB each)
            </p>
            <input
              type="file"
              multiple
              accept=".pdf,.docx,.txt,.md"
              onChange={handleFileUpload}
              className="hidden"
              id="file-upload"
            />
            <label
              htmlFor="file-upload"
              className="inline-block mt-4 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition cursor-pointer"
            >
              Select Files
            </label>
          </div>

          {/* File List */}
          {files.length > 0 && (
            <div className="mt-6">
              <h3 className="text-sm font-medium mb-3">Selected Files ({files.length})</h3>
              <div className="space-y-2">
                {files.map((file, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                  >
                    <div className="flex items-center gap-3">
                      <FileText className="h-5 w-5 text-purple-600" />
                      <div>
                        <p className="text-sm font-medium">{file.name}</p>
                        <p className="text-xs text-gray-500">
                          {(file.size / 1024 / 1024).toFixed(2)} MB
                        </p>
                      </div>
                    </div>
                    <button
                      onClick={() => removeFile(index)}
                      className="p-2 hover:bg-gray-200 rounded-full transition"
                    >
                      <Trash2 className="h-4 w-4 text-gray-500" />
                    </button>
                  </div>
                ))}
              </div>

              <button
                onClick={handleTrainModel}
                disabled={uploading || files.length === 0}
                className="w-full mt-4 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition flex items-center justify-center gap-2 disabled:opacity-50"
              >
                {uploading ? (
                  <>
                    <Loader2 className="h-5 w-5 animate-spin" />
                    Processing...
                  </>
                ) : (
                  <>
                    <Zap className="h-5 w-5" />
                    Start Training
                  </>
                )}
              </button>
            </div>
          )}
        </div>

        {/* Training Tips */}
        <div className="bg-purple-50 rounded-xl p-6">
          <h3 className="font-semibold text-purple-900 mb-3">Tips for Best Results</h3>
          <ul className="space-y-2 text-sm text-purple-800">
            <li className="flex items-start gap-2">
              <span className="text-purple-600 mt-1">•</span>
              Upload 5-10 documents for optimal training
            </li>
            <li className="flex items-start gap-2">
              <span className="text-purple-600 mt-1">•</span>
              Include past proposals, case studies, and marketing content
            </li>
            <li className="flex items-start gap-2">
              <span className="text-purple-600 mt-1">•</span>
              Training typically takes 2-5 minutes
            </li>
          </ul>
        </div>
      </main>
    </div>
  )
}

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    not_started: 'bg-gray-100 text-gray-700',
    training: 'bg-yellow-100 text-yellow-700',
    ready: 'bg-green-100 text-green-700'
  }

  const labels: Record<string, string> = {
    not_started: 'Not Trained',
    training: 'Training...',
    ready: 'Ready'
  }

  return (
    <span className={`px-3 py-1 rounded-full text-xs font-medium ${styles[status]}`}>
      {labels[status]}
    </span>
  )
}
