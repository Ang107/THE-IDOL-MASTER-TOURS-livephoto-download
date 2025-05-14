'use client'

import { useState, useCallback } from 'react'
import { useDropzone, FileRejection } from 'react-dropzone'
const MAX_FILES = 10

interface ValidateResponse {
  ok: boolean
  ticket?: string
  count?: number
  errors?: string[]
}

export default function Home() {
  // バリデーション関連ステート
  const [errors, setErrors] = useState<string[]>([])
  const [ticket, setTicket] = useState<string | null>(null)
  const [files, setFiles] = useState<File[]>([])
  const [previews, setPreviews] = useState<string[]>([])
  const [isValidating, setIsValidating] = useState(false)
  const [validationDone, setValidationDone] = useState(false)

  // ダウンロード関連ステート
  const [isDownloading, setIsDownloading] = useState(false)
  const [downloadDone, setDownloadDone] = useState(false)
  const [downloadError, setDownloadError] = useState<string | null>(null)
  const [showErrorModal, setShowErrorModal] = useState(false)
  const [downloadProgress, setDownloadProgress] = useState(0)

  // モーダル表示
  const [showModal, setShowModal] = useState(false)

  // ファイルドロップハンドラ
  const onDrop = useCallback(
    (accepted: File[], fileRejections: FileRejection[]) => {
      if (files.length + accepted.length > MAX_FILES || fileRejections.length > MAX_FILES){
        setErrors([`選択できる画像は最大 ${MAX_FILES} 枚までです。`])
        return
      }
      const newFiles = [...files, ...accepted].slice(0, MAX_FILES)
      setErrors([])          
      setTicket(null)
      setValidationDone(false)
      setDownloadDone(false)
      setDownloadProgress(0)
      setFiles(newFiles)
      setPreviews(newFiles.map((f) => URL.createObjectURL(f)))
    },
    [files]
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: { 'image/*': ['.jpeg', '.jpg', '.png', '.heic', '.heif'] },
    maxFiles: MAX_FILES,
    onDrop,
    disabled: isValidating || isDownloading,
  })

  // プレビュー削除
  const removeFile = (idx: number) => {
    const newFiles = files.filter((_, i) => i !== idx)
    setErrors([])
    setTicket(null)
    setValidationDone(false)
    setDownloadDone(false)
    setDownloadProgress(0)
    setFiles(newFiles)
    setPreviews(newFiles.map((f) => URL.createObjectURL(f)))
  }

  // 全てクリア
  const clearAll = () => {
    setFiles([])
    setPreviews([])
    setErrors([])
    setTicket(null)
    setValidationDone(false)
    setDownloadDone(false)
    setDownloadProgress(0)
  }

  // スピナーコンポーネント
  const Spinner = () => (
    <svg
      className="animate-spin h-5 w-5 mr-2 text-current"
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
    >
      <circle
        className="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="4"
      />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"
      />
    </svg>
  )

  // 検証処理
  const handleValidate = async () => {
    if (files.length === 0) return
    setErrors([])
    setTicket(null)
    setIsValidating(true)
    setValidationDone(false)
    setDownloadDone(false)
    setDownloadProgress(0)

    const fd = new FormData()
    files.forEach((f) => fd.append('files', f))

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

  // ダウンロード処理（進捗付き）
  const handleDownload = async () => {
    if (!ticket) return
    setIsDownloading(true)
    setDownloadError(null)
    setDownloadProgress(0)

    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE}/download/${ticket}`
      )
      if (!res.ok) {
        const body = await res.json()
        setDownloadError(body.error || 'ダウンロードに失敗しました。')
        setShowErrorModal(true)
      } else if (res.body) {
        const reader = res.body.getReader()
        const contentLengthHeader = res.headers.get('Content-Length')
        const total = contentLengthHeader
          ? parseInt(contentLengthHeader, 10)
          : NaN
        let received = 0
        const chunks: Uint8Array[] = []

        while (true) {
          const { done, value } = await reader.read()
          if (done) break
          if (value) {
            chunks.push(value)
            received += value.length
            if (!isNaN(total)) {
              setDownloadProgress(
                Math.floor((received / total) * 100)
              )
            }
          }
        }

        const blob = new Blob(chunks)
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        const disposition = res.headers.get("Content-Disposition")
        let filename = `idolmaster_tours_livephoto_${Date.now()}.zip`  // フォールバック
        if (disposition) {
          const match = disposition.match(/filename="(.+)"/)
          if (match) filename = match[1]
        }
        a.href = url
        a.download = filename
        document.body.appendChild(a)
        a.click()
        a.remove()
        URL.revokeObjectURL(url)

        setDownloadDone(true)
        setDownloadProgress(100)
      }
    } catch {
      setDownloadError('ネットワークエラーが発生しました。')
      setShowErrorModal(true)
    } finally {
      setIsDownloading(false)
    }
  }

  return (
    <div className="max-w-screen-md mx-auto p-4">
      {/* ヘッダー */}
      <div className="relative flex justify-center items-center mb-6">
        {/* タイトル */}
        <h1 className="text-xl sm:text-3xl font-bold text-center">
          <span className="block sm:inline">ツアマス ライブフォト</span>
          <span className="block sm:inline">Downloader</span>
        </h1>

        {/* 使い方ボタン */}
        <button
          onClick={() => setShowModal(true)}
          className="absolute right-0 px-3 py-1 bg-gray-200 rounded hover:bg-gray-300 text-sm"
        >
          使い方
        </button>
      </div>

      {/* 使い方モーダル */}
      {showModal && (
        <div className="fixed inset-0 flex justify-center items-center z-50 bg-gray-500/50">
          <div
            className="bg-white/90 rounded-lg p-6 max-w-md w-full shadow-lg"
            role="dialog"
            aria-modal="true"
          >
            <h2 className="text-xl font-semibold mb-4">使い方</h2>
            <ol className="list-decimal ml-5 space-y-2 text-sm text-gray-700">
              <li>
                ツアマスのライブフォトのQRコードが映った画像を選択します。最大{MAX_FILES}枚まで選択可能です。
              </li>
              <li>「検証する」をクリックします。</li>
              <li>
                選択された画像が検証され、エラーがある場合は一覧で表示されます。
              </li>
              <li>
                「ダウンロード」ボタンからライブフォトをまとめたzipファイルを
                ダウンロードすることができます。
              </li>
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

      {/* ダウンロードエラーモーダル */}
      {showErrorModal && downloadError && (
        <div className="fixed inset-0 flex justify-center items-center z-50 bg-gray-500/50">
          <div
            className="bg-white/90 rounded-lg p-6 max-w-sm w-full shadow-lg"
            role="alertdialog"
            aria-modal="true"
          >
            <h2 className="text-xl font-semibold mb-4">
              ダウンロードエラー
            </h2>
            <p className="text-red-600 mb-4">{downloadError}</p>
            <div className="text-right">
              <button
                onClick={() => setShowErrorModal(false)}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                閉じる
              </button>
            </div>
          </div>
        </div>
      )}
      {/* ドロップゾーン & 全てクリア */}
      <div className="mb-4">
        {/* クリアボタンを dropzone の外側右上に */}
        <div className="flex justify-end mb-1">
          <button
            onClick={clearAll}
            disabled={files.length === 0 || isValidating || isDownloading}
            className="px-3 py-1 bg-red-500 text-white rounded hover:bg-red-600 text-sm disabled:opacity-50 disabled:cursor-not-allowed"
          >
            全てクリア
          </button>
        </div>
        {/* ドロップゾーン */}
        <div
          {...getRootProps()}
          className={
            `border-2 border-dashed p-6 rounded-lg transition-colors ` +
            (isDragActive
              ? 'border-blue-500 bg-blue-50'
              : 'border-gray-300 bg-white') +
            (isValidating || isDownloading
              ? ' opacity-50 pointer-events-none'
              : '')
          }
        >
          <input {...getInputProps()} />
          <p className="text-center text-gray-600">
            {isDragActive
              ? 'ここにドロップしてください...'
              : '画像をドラッグ＆ドロップ、またはクリックして選択'}
          </p>
          <p className="mt-2 text-sm text-gray-500">
            選択中: {files.length} / {MAX_FILES} 枚
          </p>
        </div>
      </div>
      {/* サムネイルグリッド */}
      {previews.length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4 my-6">
          {previews.map((src, i) => (
            <div
              key={i}
              className="relative overflow-hidden rounded-lg bg-gray-100"
            >
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

      {/* アクションボタン */}
      <div className="flex flex-col space-y-4 mb-6 items-center">
        <button
          onClick={handleValidate}
          disabled={
            files.length === 0 || isValidating || isDownloading
          }
          className="inline-flex items-center justify-center px-6 py-2 min-w-[200px] bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <span className="relative z-10 flex items-center">
            {isValidating && <Spinner />}
            {isValidating ? '検証中...' : '検証する'}
          </span>
        </button>
        <button
          onClick={handleDownload}
          disabled={!ticket || isDownloading || downloadDone}
          className="inline-flex items-center justify-center px-6 py-2 min-w-[200px] bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed overflow-hidden"
        >
          {isDownloading && <Spinner />}
          <span className="ml-2">
            {isDownloading
              ? `ダウンロード中…${downloadProgress}%完了`
              : downloadDone
              ? 'ダウンロード完了'
              : 'ダウンロード'}
          </span>
        </button>
      </div>

      {/* 検証サマリー */}
      {validationDone && (
        <div className="mb-6 text-center text-gray-700">
          <p>全ての画像の検証が終了しました。</p>
          {errors.length === 0 ? (
            <p className="mt-2 text-green-600">
              全ての画像の読み取りに成功しました。
            </p>
          ) : errors.length === files.length ? (
            <p className="mt-2 text-red-600">
              以下のような原因で全ての画像でエラーが発生しました。
            </p>
          ) : (
            <p className="mt-2 text-yellow-600">
              以下のような原因で一部の画像でエラーが発生しました。
            </p>
          )}
        </div>
      )}

      {/* エラー一覧 */}
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
