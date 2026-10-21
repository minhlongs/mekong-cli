'use client'

import { useCallback, useState } from 'react'

/**
 * Export Utilities Hook — CSV, JSON, PDF print, and Clipboard copy
 */
interface UseExportOptions {
  filename?: string
  onExportStart?: () => void
  onExportComplete?: (format: string) => void
  onExportError?: (error: Error) => void
}

export function useExport(options: UseExportOptions = {}) {
  const [isExporting, setIsExporting] = useState(false)
  const { filename = 'export', onExportStart, onExportComplete, onExportError } = options

  const exportToCSV = useCallback(
    (data: Record<string, unknown>[], customFilename?: string) => {
      try {
        setIsExporting(true)
        onExportStart?.()
        if (!data || data.length === 0) throw new Error('No data to export')

        const headers = Object.keys(data[0])
        const csvRows = [
          headers.join(','),
          ...data.map(row =>
            headers
              .map(header => {
                const stringValue = String(row[header] ?? '')
                return stringValue.includes(',') || stringValue.includes('"')
                  ? `"${stringValue.replace(/"/g, '""')}"`
                  : stringValue
              })
              .join(',')
          ),
        ]

        const blob = new Blob([csvRows.join('\n')], { type: 'text/csv;charset=utf-8;' })
        downloadBlob(blob, `${customFilename || filename}.csv`)
        onExportComplete?.('csv')
      } catch (error) {
        onExportError?.(error as Error)
      } finally {
        setIsExporting(false)
      }
    },
    [filename, onExportStart, onExportComplete, onExportError]
  )

  const exportToJSON = useCallback(
    (data: unknown, customFilename?: string) => {
      try {
        setIsExporting(true)
        onExportStart?.()
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
        downloadBlob(blob, `${customFilename || filename}.json`)
        onExportComplete?.('json')
      } catch (error) {
        onExportError?.(error as Error)
      } finally {
        setIsExporting(false)
      }
    },
    [filename, onExportStart, onExportComplete, onExportError]
  )

  const exportToPDF = useCallback(
    (elementId?: string) => {
      try {
        setIsExporting(true)
        onExportStart?.()
        if (elementId) {
          const element = document.getElementById(elementId)
          const printWindow = element ? window.open('', '_blank') : null
          if (element && printWindow) {
            const doc = printWindow.document
            doc.title = filename
            const style = doc.createElement('style')
            style.textContent =
              'body{font-family:system-ui,sans-serif;padding:20px}@media print{body{padding:0}}'
            doc.head.appendChild(style)
            doc.body.replaceChildren(element.cloneNode(true))
            printWindow.print()
          }
        } else {
          window.print()
        }
        onExportComplete?.('pdf')
      } catch (error) {
        onExportError?.(error as Error)
      } finally {
        setIsExporting(false)
      }
    },
    [filename, onExportStart, onExportComplete, onExportError]
  )

  const copyToClipboard = useCallback(
    async (data: unknown) => {
      try {
        setIsExporting(true)
        const text = typeof data === 'string' ? data : JSON.stringify(data, null, 2)
        await navigator.clipboard.writeText(text)
        onExportComplete?.('clipboard')
      } catch (error) {
        onExportError?.(error as Error)
      } finally {
        setIsExporting(false)
      }
    },
    [onExportComplete, onExportError]
  )

  return { isExporting, exportToCSV, exportToJSON, exportToPDF, copyToClipboard }
}

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

export function getExportFilename(prefix: string): string {
  return `${prefix}_${new Date().toISOString().split('T')[0]}`
}

export default useExport
