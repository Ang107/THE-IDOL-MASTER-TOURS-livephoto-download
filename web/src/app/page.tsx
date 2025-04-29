'use client'

import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'

interface ValidateResponse {
  ok: boolean
  ticket?: string
  count?: number
  errors?: string[]
}

export default function Home() {
  const [errors, setErrors] = useState<string[]>([])
  const [ticket, setTicket] = useState<string | null>(null)
  const [files, setFiles] = useState<File[]>([])
  const [previews, setPreviews] = useState<string[]>([])
  const [isValidating, setIsValidating] = useState(false)
  const [showModal, setShowModal] = useState(false)
  const [validationDone, setValidationDone] = useState(false)

  // Drag & drop / file select handler
  const onDrop = useCallback((accepted: File[]) => {
    if (accepted.length + files.length > 10) return
    const newFiles = [...files, ...accepted].slice(0, 10)
    setErrors([])
    setTicket(null)
    setValidationDone(false)
    setFiles(newFiles)
    setPreviews(newFiles.map(f => URL.createObjectURL(f)))
  }, [files])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: { 'image/*': ['.jpeg', '.jpg', '.png', '.heic', '.heif'] },
    maxFiles: 10,
    onDrop,
    disabled: isValidating
  })

  const removeFile = (idx: number) => {
    const newFiles = files.filter((_, i) => i !== idx)
    setValidationDone(false)
    setFiles(newFiles)
    setPreviews(newFiles.map(f => URL.createObjectURL(f)))
  }

  const clearAll = () => {
    setFiles([])
    setPreviews([])
    setErrors([])
    setTicket(null)
    setValidationDone(false)
  }

  const handleValidate = async () => {
    if (files.length === 0) return
    setErrors([])
    setTicket(null)
    setIsValidating(true)
    setValidationDone(false)

    const fd = new FormData()
    files.forEach(f => fd.append('files', f))

    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE}/validate`,
        { method: 'POST', body: fd }
      )
      const body: ValidateResponse = await res.json()
      if (!body.ok) {
        setErrors(body.errors || ['不明なエラーが発生しました。'])
      } else {
        setErrors(body.errors || [])
        setTicket(body.ticket || null)
      }
    } catch {
      setErrors(['ネットワークエラーが発生しました。'])
    } finally {
      setIsValidating(false)
      setValidationDone(true)
    }
  }

  const handleDownload = () => {
    if (ticket) {
      window.open(
        `${process.env.NEXT_PUBLIC_API_BASE}/download/${ticket}`,
        '_blank'
      )
    }
  }

  return (
    <div className="container mx-auto p-4">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-center flex-1">
          ツアマス ライブフォト Downloader
        </h1>
        <button
          onClick={() => setShowModal(true)}
          className="ml-4 px-3 py-1 bg-gray-200 rounded hover:bg-gray-300 text-sm"
        >
          使い方
        </button>
      </div>

      {/* Usage Modal */}
      {showModal && (
        <div className="fixed inset-0 flex justify-center items-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full shadow-lg">
            <h2 className="text-xl font-semibold mb-4">使い方</h2>
            <ol className="list-decimal ml-5 space-y-2 text-sm text-gray-700">
              <li>ツアマスのライブフォトのQRコードが映った画像を選択します。最大10枚まで選択可能です。</li>
              <li>「検証する」をクリックします。</li>
              <li>選択された画像が検証され、エラーがある場合は一覧で表示されます。</li>
              <li>「ダウンロード」ボタンからライブフォトをまとめたzipファイルをダウンロードすることができます。</li>
            </ol>
            <div className="mt-6 text-right">
              <button
                onClick={() => setShowModal(false)}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                閉じる
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Dropzone & Clear All */}
      <div className="flex items-start mb-2">
        <div
          {...getRootProps()}
          className={
            `border-2 border-dashed p-6 rounded-lg transition-colors flex-1 mr-4 ` +
            (isDragActive
              ? 'border-blue-500 bg-blue-50'
              : 'border-gray-300 bg-white') +
            (isValidating ? ' opacity-50 pointer-events-none' : '')
          }
        >
          <input {...getInputProps()} />
          <p className="text-center text-gray-600">
            {isDragActive
              ? 'ここにドロップしてください...' 
              : '画像をドラッグ＆ドロップ、またはクリックして選択'}
          </p>
          <p className="mt-2 text-sm text-gray-500">
            選択中: {files.length} / 10 枚
          </p>
        </div>
        <button
          onClick={clearAll}
          disabled={files.length === 0 || isValidating}
          className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600 transition disabled:opacity-50 disabled:cursor-not-allowed"
        >
          選択した画像を全てクリア
        </button>
      </div>

      {/* Thumbnails grid */}
      {previews.length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4 my-6">
          {previews.map((src, i) => (
            <div key={i} className="relative overflow-hidden rounded-lg bg-gray-100">
              <img
                src={src}
                alt={`preview ${i + 1}`}
                className="block w-full max-h-32 object-contain"
              />
              <button
                onClick={() => removeFile(i)}
                className="absolute top-1 right-1 bg-white rounded-full p-1 shadow hover:bg-gray-200"
                aria-label="ファイルを削除"
              >
                ×
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Action buttons stacked */}
      <div className="space-y-4 mb-6">
        <button
          onClick={handleValidate}
          disabled={files.length === 0 || isValidating}
          className="w-full px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isValidating ? '検証中...' : '検証する'}
        </button>
        <button
          onClick={handleDownload}
          disabled={!ticket}
          className="w-full px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
        >
          ダウンロード
        </button>
      </div>

      {/* Validation summary */}
      {validationDone && (
        <div className="mb-6 text-center text-gray-700">
          <p>全ての画像の検証が終了しました。</p>
          {errors.length === 0 ? (
            <p className="mt-2 text-green-600">全ての画像の読み取りに成功しました。</p>
          ) : errors.length === files.length ? (
            <p className="mt-2 text-red-600">以下のような原因で全ての画像でエラーが発生しました。</p>
          ) : (
            <p className="mt-2 text-yellow-600">以下のような原因で一部の画像でエラーが発生しました。</p>
          )}
        </div>
      )}

      {/* Error display */}
      {errors.length > 0 && (
        <div className="mt-6 space-y-2">
          {errors.map((err, i) => (
            <div
              key={i}
              className="p-4 bg-red-50 border-l-4 border-red-500 text-red-700 rounded-md"
            >
              {err}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
