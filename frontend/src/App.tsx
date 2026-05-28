import { useState, useEffect, useRef, useCallback } from 'react'

// ── Types ──────────────────────────────────────────────────────────────────

type Tab = 'practice' | 'import' | 'history'

interface Sentence {
  en: string
  zh: string
  start: number
  end: number
}

interface HistoryItem {
  date: string
  video: string
  video_id: string
  sentences: number
  practiced: number
  avg_score: number
}

interface VideoInfo {
  id: string
  name: string
  duration: string
  status: string
}

interface ScoreResult {
  pronunciation: number
  fluency: number
  timing: number
  completeness: number
  overall: number
}

// ── API ────────────────────────────────────────────────────────────────────

async function api<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init)
  if (!res.ok) throw new Error(`${res.status}: ${res.statusText}`)
  return res.json()
}

// ── Helpers ────────────────────────────────────────────────────────────────

function medalDisplay(score: number) {
  if (score >= 80) return { emoji: '🥇', text: String(score), cls: 'text-amber-600 bg-amber-50 border-amber-300' }
  if (score >= 60) return { emoji: '🥈', text: String(score), cls: 'text-slate-500 bg-slate-50 border-slate-300' }
  return { emoji: '🥉', text: '继续加油', cls: 'text-rose-500 bg-rose-50 border-rose-200' }
}

// ── Score Ring Component ───────────────────────────────────────────────────
// (removed — kept in git history)

// ── Waveform ───────────────────────────────────────────────────────────────

function WaveformBars({ count }: { count: number }) {
  return (
    <div className="flex items-center gap-[2px] h-8">
      {Array.from({ length: count }, (_, i) => (
        <div
          key={i}
          className="w-[2px] rounded-full bg-gradient-to-t from-coral to-orange-300"
          style={{ height: `${Math.floor(Math.random() * 20) + 6}px`, opacity: i < count / 2 ? 0.7 : 0.15 }}
        />
      ))}
    </div>
  )
}

function Waveform() {
  return (
    <div className="flex-1 flex items-center gap-[2px] h-10">
      {Array.from({ length: 48 }, () => Math.floor(Math.random() * 28) + 6).map((h, i) => (
        <div
          key={i}
          className="w-[3px] rounded-full bg-gradient-to-t from-coral to-orange-300 transition-all"
          style={{ height: `${h}px`, opacity: i < 20 ? 0.7 : 0.15 }}
        />
      ))}
    </div>
  )
}

// ── Navbar ─────────────────────────────────────────────────────────────────

function Navbar({ active, onTabChange }: { active: Tab; onTabChange: (t: Tab) => void }) {
  const tabs: { id: Tab; label: string; short: string }[] = [
    { id: 'import', label: '📁 导入视频', short: '📁' },
    { id: 'practice', label: '🎯 跟读练习', short: '🎯' },
    { id: 'history', label: '📊 学习记录', short: '📊' },
  ]

  return (
    <header className="sticky top-0 z-50 bg-white/95 backdrop-blur-xl border-b border-amber-100">
      <div className="max-w-7xl mx-auto px-4 md:px-8 h-14 md:h-16 flex items-center gap-3 md:gap-10">
        <div className="flex items-center gap-2 md:gap-2.5 text-lg md:text-xl font-bold tracking-tight select-none shrink-0">
          <span className="text-xl md:text-2xl">🎤</span>
          <span className="text-coral-dark">Read</span>
          <span className="text-slate-600">AfterMe</span>
        </div>
        <nav className="flex items-center gap-0.5 md:gap-1 overflow-x-auto w-full justify-end md:justify-start">
          {tabs.map((t) => (
            <button
              key={t.id}
              onClick={() => onTabChange(t.id)}
              className={`min-h-10 px-2.5 md:px-4 py-2 rounded-lg text-xs md:text-sm font-medium transition-all duration-200 whitespace-nowrap ${
                active === t.id
                  ? 'text-coral-dark bg-coral/10'
                  : 'text-slate-400 hover:text-slate-600 hover:bg-amber-50'
              }`}
            >
              <span className="md:hidden">{t.short}</span>
              <span className="hidden md:inline">{t.label}</span>
            </button>
          ))}
        </nav>
      </div>
    </header>
  )
}

// ── Import Page ────────────────────────────────────────────────────────────

function ImportPage({ videos, onVideosChange, onStartPractice }: {
  videos: VideoInfo[]
  onVideosChange: () => void
  onStartPractice: (id: string, name: string) => void
}) {
  const [uploading, setUploading] = useState(false)
  const [processingId, setProcessingId] = useState<string | null>(null)
  const [processingStep, setProcessingStep] = useState('')
  const [dragOver, setDragOver] = useState(false)
  const fileRef = useRef<HTMLInputElement>(null)
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const processingNameRef = useRef('')

  const handleDelete = useCallback(async (id: string, name: string) => {
    if (!window.confirm(`确定删除「${name}」及其所有练习记录？`)) return
    try {
      await fetch(`/api/videos/${id}`, { method: 'DELETE' })
      onVideosChange()
    } catch {
      alert('删除失败')
    }
  }, [onVideosChange])

  const pickAndUploadFile = useCallback(() => {
    fileRef.current?.click()
  }, [])

  // Poll processing status
  useEffect(() => {
    if (!processingId) {
      if (pollRef.current) clearInterval(pollRef.current)
      return
    }
    pollRef.current = setInterval(async () => {
      try {
        const res = await fetch(`/api/videos/${processingId}/status`)
        if (!res.ok) throw new Error()
        const data = await res.json()
        if (data.status === '已处理' || data.done) {
          clearInterval(pollRef.current!)
          setProcessingId(null)
          setUploading(false)
          onVideosChange()
          onStartPractice(processingId, processingNameRef.current)
        } else {
          setProcessingStep(data.step || '处理中...')
        }
      } catch {
        clearInterval(pollRef.current!)
        setProcessingId(null)
        setUploading(false)
      }
    }, 2000)
    return () => { if (pollRef.current) clearInterval(pollRef.current) }
  }, [processingId, onVideosChange, onStartPractice])

  const doUpload = useCallback(async (file: File) => {
    if (!file.name.match(/\.(mp4|avi|mov|mkv|webm)$/i)) {
      alert('不支持的文件格式。支持: mp4, avi, mov, mkv, webm')
      return
    }
    processingNameRef.current = file.name.replace(/\.[^.]+$/, '')
    setUploading(true)
    try {
      const form = new FormData()
      form.append('file', file)
      const res = await fetch('/api/upload', { method: 'POST', body: form })
      if (!res.ok) throw new Error(`上传失败: ${res.status}`)
      const result = await res.json()
      setProcessingId(result.video_id)
      setProcessingStep('排队中...')
      onVideosChange()
    } catch (e: any) {
      alert('上传失败: ' + (e.message || '未知错误'))
      setUploading(false)
    }
  }, [onVideosChange])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)
    const file = e.dataTransfer.files[0]
    if (file) doUpload(file)
  }, [doUpload])

  const handleZoneClick = useCallback(() => {
    if (!uploading) pickAndUploadFile()
  }, [uploading, pickAndUploadFile])

  return (
    <div className="animate-enter max-w-3xl mx-auto px-4 md:px-8 py-4 md:py-8 space-y-6 md:space-y-8">
      <div>
        <h1 className="text-xl md:text-2xl font-bold text-slate-700">导入视频</h1>
        <p className="text-xs md:text-sm text-slate-400 mt-1">上传英语视频，自动生成跟读句子</p>
      </div>

      {/* Upload zone */}
      <div
        onClick={handleZoneClick}
        onDrop={handleDrop}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
        onDragLeave={() => setDragOver(false)}
        className={`border-2 border-dashed rounded-2xl p-8 sm:p-12 md:p-16 text-center cursor-pointer transition-all duration-250 bg-white/60 ${
          dragOver
            ? 'border-coral border-4 bg-coral/5'
            : 'border-amber-200 hover:border-coral/40 hover:bg-coral/[0.02]'
        }`}
      >
        <input
          ref={fileRef}
          type="file"
          accept=".mp4,.avi,.mov,.mkv,.webm"
          className="hidden"
          onChange={(e) => { const f = e.target.files?.[0]; if (f) doUpload(f) }}
        />
        {uploading ? (
          <div className="flex flex-col items-center gap-3">
            <div className="w-10 h-10 border-4 border-coral/30 border-t-coral rounded-full animate-spin" />
            <p className="text-sm text-slate-500">正在处理视频...</p>
            {processingStep && (
              <p className="text-xs text-amber-500 font-mono">{processingStep}</p>
            )}
          </div>
        ) : (
          <>
            <div className="text-4xl md:text-5xl mb-3 md:mb-4 opacity-60">
              {dragOver ? '📥' : '📂'}
            </div>
            <p className="text-sm md:text-base text-slate-500">
              {dragOver ? '松开以上传文件' : '点击上传或拖拽视频文件到此'}
            </p>
            <p className="text-xs text-slate-400 mt-2">支持 MP4, AVI, MOV · 最大 500MB</p>
          </>
        )}
      </div>

      {/* Video list */}
      <div>
        <h2 className="text-sm md:text-base font-semibold text-slate-600 mb-3 md:mb-4">已导入视频</h2>
        {videos.length === 0 ? (
          <p className="text-xs text-slate-400 text-center py-8">暂无视频，请上传</p>
        ) : (
          <div className="space-y-2">
            {videos.map((v) => (
              <div
                key={v.id}
                className="flex items-center gap-3 md:gap-4 px-3 md:px-4 py-3 rounded-xl bg-white border border-amber-100 shadow-sm transition-all duration-200 hover:shadow-md hover:border-amber-200"
              >
                <div className="w-10 h-7 md:w-11 md:h-8 rounded-md bg-amber-50 flex items-center justify-center text-amber-400 text-xs md:text-sm shrink-0">
                  🎬
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-xs md:text-sm text-slate-700 font-medium truncate">{v.name}</p>
                  <p className="text-[10px] md:text-xs text-slate-400 mt-0.5">时长 {v.duration}</p>
                </div>
                <span
                  className={`shrink-0 text-[10px] md:text-xs font-medium px-2 md:px-3 py-1 rounded-full border ${
                    v.status === '已处理'
                      ? 'text-emerald-600 bg-emerald-50 border-emerald-200'
                      : 'text-amber-600 bg-amber-50 border-amber-200'
                  }`}
                >
                  {v.status}
                </span>
                <button
                  onClick={() => onStartPractice(v.id, v.name)}
                  className="shrink-0 text-xs font-medium px-3 py-1.5 rounded-lg bg-coral/10 text-coral-dark hover:bg-coral/20 transition"
                >
                  练习
                </button>
                <button
                  onClick={() => handleDelete(v.id, v.name)}
                  className="shrink-0 text-xs font-medium px-2.5 py-1.5 rounded-lg text-slate-400 hover:text-rose-500 hover:bg-rose-50 transition"
                  title="删除"
                >
                  ✕
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

// ── Practice Page ──────────────────────────────────────────────────────────

function PracticePage({ selectedVideoId, selectedVideoName, onBackToImport }: {
  selectedVideoId: string | null
  selectedVideoName: string
  onBackToImport: () => void
}) {
  const [sentences, setSentences] = useState<Sentence[]>([])
  const [loading, setLoading] = useState(false)
  const [activeIdx, setActiveIdx] = useState(0)
  const [scoring, setScoring] = useState(false)
  const [sentenceScores, setSentenceScores] = useState<Record<number, ScoreResult>>({})
  const [recording, setRecording] = useState(false)
  const mediaRecorder = useRef<MediaRecorder | null>(null)
  const audioChunks = useRef<Blob[]>([])
  const [recordedBlob, setRecordedBlob] = useState<Blob | null>(null)
  const recordedUrlRef = useRef<string | null>(null)
  const [recordedDuration, setRecordedDuration] = useState(0)
  const [recordingDuration, setRecordingDuration] = useState(0)
  const recTimer = useRef<ReturnType<typeof setInterval> | null>(null)
  const playTimer = useRef<ReturnType<typeof setInterval> | null>(null)
  const autoStopTimer = useRef<ReturnType<typeof setTimeout> | null>(null)
  const videoRef = useRef<HTMLVideoElement | null>(null)
  const [playing, setPlaying] = useState(false)
  const [playbackPosition, setPlaybackPosition] = useState(0)
  const audioPlayer = useRef<HTMLAudioElement | null>(null)
  const recordingMeta = useRef<{videoId: string; sentenceIdx: number} | null>(null)

  // Fetch sentences when video is selected
  useEffect(() => {
    if (!selectedVideoId) {
      setSentences([])
      return
    }
    setLoading(true)
    api<{video_id: string; video_name: string; sentences: Sentence[]}>(
      `/api/videos/${selectedVideoId}/sentences`
    ).then(data => {
      setSentences(data.sentences)
      setActiveIdx(0)
      setSentenceScores({})
      setRecordedBlob(null)
      setRecordedDuration(0)
      setPlaybackPosition(0)
      if (playTimer.current) clearInterval(playTimer.current)
      // Load saved scores for this video
      fetch(`/api/recordings/${selectedVideoId}/scores`)
        .then(r => r.json())
        .then(scores => {
          const parsed: Record<number, ScoreResult> = {}
          for (const [k, v] of Object.entries(scores)) {
            parsed[Number(k)] = v as ScoreResult
          }
          setSentenceScores(parsed)
        })
        .catch(() => {})
    }).catch(() => {
      setSentences([])
    }).finally(() => setLoading(false))
  }, [selectedVideoId])

  // Load saved recording when switching sentences
  useEffect(() => {
    if (!selectedVideoId || sentences.length === 0) return
    const idx = activeIdx
    const loadSaved = async () => {
      try {
        const resp = await fetch(`/api/recordings/${selectedVideoId}/${idx}/file`)
        if (!resp.ok) {
          setRecordedBlob(null)
          setRecordedDuration(0)
          return
        }
        const blob = await resp.blob()
        if (recordedUrlRef.current) URL.revokeObjectURL(recordedUrlRef.current)
        recordedUrlRef.current = URL.createObjectURL(blob)
        setRecordedBlob(blob)
        const audio = new Audio(recordedUrlRef.current)
        audio.onloadedmetadata = () => {
          setRecordedDuration(Math.floor(audio.duration))
          audio.remove()
        }
      } catch {
        setRecordedBlob(null)
        setRecordedDuration(0)
      }
    }
    loadSaved()
  }, [selectedVideoId, activeIdx, sentences.length])

  // Auto-highlight + pause at end of current sentence
  const onTimeUpdate = () => {
    if (!videoRef.current || sentences.length === 0) return
    const t = videoRef.current.currentTime
    const cur = sentences[activeIdx]
    if (cur && t >= cur.end && t < cur.end + 0.5) {
      videoRef.current.pause()
      return
    }
    const idx = sentences.findIndex(s => t >= s.start && t < s.end)
    if (idx >= 0 && idx !== activeIdx) {
      setActiveIdx(idx)
    }
  }

  // Seek to a specific sentence
  const seekToSentence = (idx: number) => {
    if (!videoRef.current || !sentences[idx]) return
    setActiveIdx(idx)
    videoRef.current.currentTime = sentences[idx].start
    videoRef.current.play()
  }

  // ── Recording ────────────────────────────────────────────────────────────

  const startRecording = async () => {
    try {
      if (window.location.protocol !== 'https:' && window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
        const ok = confirm('录音需要 HTTPS 连接。\n\n是否继续尝试？')
        if (!ok) return
      }
      if (audioPlayer.current) {
        audioPlayer.current.pause()
        audioPlayer.current = null
      }
      setPlaying(false)
      setPlaybackPosition(0)
      if (playTimer.current) clearInterval(playTimer.current)

      videoRef.current?.pause()
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mimeTypes = ['audio/webm;codecs=opus', 'audio/webm', 'audio/ogg;codecs=opus', '']
      const mrType = mimeTypes.find(t => MediaRecorder.isTypeSupported(t)) || ''
      const mr = new MediaRecorder(stream, mrType ? { mimeType: mrType } : undefined)
      mediaRecorder.current = mr
      audioChunks.current = []
      recordingMeta.current = { videoId: selectedVideoId!, sentenceIdx: activeIdx }
      setRecordedBlob(null)
      setRecordedDuration(0)

      mr.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunks.current.push(e.data)
      }

      mr.onstop = () => {
        stream.getTracks().forEach(t => t.stop())
        const blob = new Blob(audioChunks.current, { type: mrType || 'audio/webm' })
        if (recordedUrlRef.current) URL.revokeObjectURL(recordedUrlRef.current)
        recordedUrlRef.current = URL.createObjectURL(blob)
        setRecordedBlob(blob)

        const meta = recordingMeta.current
        if (meta) {
          // Save recording
          const saveForm = new FormData()
          saveForm.append('video_id', meta.videoId)
          saveForm.append('sentence_index', String(meta.sentenceIdx))
          saveForm.append('file', blob, `recording_${meta.sentenceIdx}.webm`)
          fetch('/api/recordings', { method: 'POST', body: saveForm }).catch(() => {})

          // Auto-score
          setScoring(true)
          const scoreForm = new FormData()
          scoreForm.append('video_id', meta.videoId)
          scoreForm.append('sentence_index', String(meta.sentenceIdx))
          scoreForm.append('age_group', 'child')
          scoreForm.append('file', blob, `recording_${meta.sentenceIdx}.webm`)
          api<ScoreResult>('/api/score', { method: 'POST', body: scoreForm })
            .then(result => {
              setSentenceScores(prev => ({ ...prev, [meta.sentenceIdx]: result }))
              // Persist score
              fetch('/api/recordings/score', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                  video_id: meta.videoId,
                  sentence_index: meta.sentenceIdx,
                  score: result,
                }),
              }).catch(() => {})
            })
            .catch(() => {})
            .finally(() => setScoring(false))
        }
      }

      mr.start()
      setRecording(true)
      const startTime = Date.now()
      recTimer.current = setInterval(() => {
        setRecordingDuration(Math.floor((Date.now() - startTime) / 1000))
      }, 200)
      const sentence = sentences[activeIdx]
      if (sentence) {
        const maxDuration = Math.ceil(sentence.end - sentence.start) + 1
        autoStopTimer.current = setTimeout(() => {
          if (mediaRecorder.current?.state === 'recording') {
            stopRecording()
          }
        }, maxDuration * 1000)
      }
    } catch (e: any) {
      const msg = e?.name || e?.message || '未知错误'
      if (msg === 'NotAllowedError') {
        alert('麦克风权限被拒绝')
      } else if (msg === 'NotFoundError') {
        alert('未找到麦克风设备')
      } else {
        alert('无法访问麦克风: ' + msg)
      }
    }
  }

  const stopRecording = () => {
    setRecordedDuration(recordingDuration)
    mediaRecorder.current?.stop()
    setRecording(false)
    if (recTimer.current) clearInterval(recTimer.current)
    if (autoStopTimer.current) clearTimeout(autoStopTimer.current)
  }

  const playRecording = () => {
    const url = recordedUrlRef.current
    if (!url) return
    if (playing) {
      audioPlayer.current?.pause()
      setPlaying(false)
      if (playTimer.current) clearInterval(playTimer.current)
      return
    }
    const audio = new Audio(url)
    audioPlayer.current = audio
    audio.onended = () => {
      setPlaying(false)
      setPlaybackPosition(0)
      if (playTimer.current) clearInterval(playTimer.current)
    }
    audio.onpause = () => {
      setPlaying(false)
    }
    audio.play().then(() => {
      setPlaying(true)
      setPlaybackPosition(0)
      if (playTimer.current) clearInterval(playTimer.current)
      playTimer.current = setInterval(() => {
        setPlaybackPosition(Math.floor(audio.currentTime))
      }, 200)
    }).catch(() => {})
  }

  // No video selected — prompt user
  if (!selectedVideoId) {
    return (
      <div className="animate-enter max-w-3xl mx-auto px-4 md:px-8 py-16 text-center">
        <div className="text-5xl mb-4 opacity-60">🎯</div>
        <h2 className="text-lg font-semibold text-slate-600">请先导入一个视频</h2>
        <p className="text-sm text-slate-400 mt-2 mb-6">上传视频后才能开始跟读练习</p>
        <button
          onClick={onBackToImport}
          className="px-6 py-2.5 rounded-xl bg-coral text-white font-medium hover:bg-coral-dark transition shadow-md shadow-coral/20"
        >
          去导入视频
        </button>
      </div>
    )
  }

  const allScores = Object.entries(sentenceScores) as [string, ScoreResult][]
  const avgOverall = allScores.length > 0
    ? Math.round(allScores.reduce((s, [, v]) => s + v.overall, 0) / allScores.length)
    : 0

  return (
    <div className="animate-enter max-w-7xl mx-auto px-4 md:px-8 py-4 md:py-8 space-y-4 md:space-y-6">
      {/* Header with video name */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl md:text-2xl font-bold text-slate-700">跟读练习</h1>
          <p className="text-xs text-slate-400 mt-1 truncate max-w-[300px] md:max-w-xl">{selectedVideoName}</p>
        </div>
        <button
          onClick={onBackToImport}
          className="text-xs text-slate-400 hover:text-coral-dark transition"
        >
          切换视频
        </button>
      </div>

      <div className="flex flex-col lg:flex-row gap-4 lg:gap-6">
        {/* Left: Video + Recording */}
        <div className="w-full lg:flex-[3] flex flex-col gap-3 md:gap-4">
          {/* Video Player */}
          <div className="rounded-xl overflow-hidden bg-black border border-amber-100 shadow-sm relative group">
            <video
              ref={videoRef}
              src={`/api/videos/${selectedVideoId}/file`}
              className="w-full aspect-video object-contain bg-black"
              onTimeUpdate={onTimeUpdate}
              controls
              playsInline
            />
          </div>

          {/* Recording Bar */}
          <div className="flex items-center gap-2 md:gap-4 px-3 md:px-5 py-2.5 md:py-3.5 rounded-xl bg-white border border-amber-100 shadow-sm">
            {!recording ? (
              <button
                onClick={startRecording}
                className="w-10 h-10 md:w-11 md:h-11 rounded-full bg-gradient-to-br from-coral to-rose-400 hover:from-rose-400 hover:to-coral text-white flex items-center justify-center transition-all hover:scale-105 shrink-0 text-base md:text-lg shadow-md shadow-coral/20"
              >
                🔴
              </button>
            ) : (
              <button
                onClick={stopRecording}
                className="w-10 h-10 md:w-11 md:h-11 rounded-full bg-slate-200 hover:bg-slate-300 text-slate-500 flex items-center justify-center transition-all shrink-0 text-base md:text-lg"
              >
                ⏹
              </button>
            )}
            <button
              onClick={playRecording}
              disabled={!recordedBlob}
              className="w-10 h-10 md:w-11 md:h-11 rounded-full bg-gradient-to-br from-sky-400 to-blue-400 hover:from-blue-400 hover:to-sky-400 text-white flex items-center justify-center transition-all shrink-0 text-base md:text-lg shadow-md shadow-sky-200 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {playing ? '⏸' : '▶'}
            </button>
            <div className="hidden sm:block flex-1">
              <Waveform />
            </div>
            <div className="sm:hidden flex-1">
              <WaveformBars count={20} />
            </div>
            <span className="text-[10px] md:text-xs text-slate-400 tabular-nums shrink-0">
              {recording
                ? `00:${recordingDuration.toString().padStart(2, '0')}`
                : playing
                  ? `00:${playbackPosition.toString().padStart(2, '0')} / 00:${recordedDuration.toString().padStart(2, '0')}`
                  : recordedDuration > 0
                    ? `00:${recordedDuration.toString().padStart(2, '0')}`
                    : ''}
            </span>
            {scoring && (
              <div className="w-5 h-5 border-2 border-coral/30 border-t-coral rounded-full animate-spin shrink-0" />
            )}
            {sentenceScores[activeIdx] && !scoring && (
              <span className={`text-xs font-bold px-2 py-0.5 rounded-full border ${medalDisplay(sentenceScores[activeIdx].overall).cls}`}>
                {medalDisplay(sentenceScores[activeIdx].overall).emoji} {medalDisplay(sentenceScores[activeIdx].overall).text}
              </span>
            )}
          </div>
        </div>

        {/* Right: Sentence Panel */}
        <div className="w-full lg:flex-[2] lg:max-w-md">
          <div className="rounded-xl border border-amber-100 bg-white shadow-sm flex flex-col">
            <div className="px-4 md:px-5 py-3 md:py-4 border-b border-amber-100">
              <h3 className="text-xs md:text-sm font-semibold text-slate-700">句子列表</h3>
              {loading ? (
                <p className="text-[10px] md:text-xs text-slate-400 mt-0.5">加载中...</p>
              ) : (
                <p className="text-[10px] md:text-xs text-slate-400 mt-0.5">
                  共 {sentences.length} 句 · 当前第 {sentences.length > 0 ? activeIdx + 1 : 0} 句
                </p>
              )}
            </div>
            <div className="overflow-y-auto px-2 md:px-3 py-2 space-y-1" style={{ maxHeight: 'min(360px, 40vh)' }}>
              {loading ? (
                <p className="text-xs text-slate-400 text-center py-8">正在加载...</p>
              ) : sentences.length === 0 ? (
                <p className="text-xs text-slate-400 text-center py-8">暂无语句</p>
              ) : (
                sentences.map((s, i) => (
                  <div
                    key={i}
                    onClick={() => seekToSentence(i)}
                    className={`px-3 md:px-4 py-2.5 md:py-3 rounded-lg cursor-pointer transition-all duration-200 border flex items-start justify-between gap-2 ${
                      i === activeIdx
                        ? 'bg-coral/[0.06] border-coral/30 shadow-sm'
                        : 'bg-white border-transparent hover:bg-amber-50 hover:border-amber-200'
                    }`}
                  >
                    <div className="flex-1 min-w-0">
                      <p className={`text-xs md:text-sm leading-relaxed ${i === activeIdx ? 'text-slate-800 font-medium' : 'text-slate-600'}`}>
                        {s.en}
                      </p>
                      <p className={`text-[10px] md:text-xs mt-1 ${i === activeIdx ? 'text-slate-500' : 'text-slate-400'}`}>
                        {s.zh || ''}
                      </p>
                      <p className="text-[9px] md:text-[10px] text-slate-300 mt-1 tabular-nums">
                        {s.start.toFixed(1)}s - {s.end.toFixed(1)}s
                      </p>
                    </div>
                    {sentenceScores[i] && (
                      <span className={`shrink-0 text-xs px-2 py-0.5 rounded-full border mt-1 ${medalDisplay(sentenceScores[i].overall).cls}`}>
                        {medalDisplay(sentenceScores[i].overall).emoji} {medalDisplay(sentenceScores[i].overall).text}
                      </span>
                    )}
                  </div>
                ))
              )}
            </div>
            {allScores.length > 0 && (
              <div className="px-4 md:px-5 py-3 md:py-4 border-t border-amber-100">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-500">已评分 {allScores.length}/{sentences.length} 句</span>
                  <span className="flex items-baseline gap-1">
                    <span className="text-lg font-bold text-coral-dark">{avgOverall}</span>
                    <span className="text-xs text-slate-400">平均分</span>
                  </span>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

// ── History Page ───────────────────────────────────────────────────────────

function HistoryPage({ history, onStartPractice }: { history: HistoryItem[]; onStartPractice: (id: string, name: string) => void }) {
  return (
    <div className="animate-enter max-w-3xl mx-auto px-4 md:px-8 py-4 md:py-8 space-y-4 md:space-y-6">
      <div>
        <h1 className="text-xl md:text-2xl font-bold text-slate-700">学习记录</h1>
        <p className="text-xs md:text-sm text-slate-400 mt-1">查看你的练习历史和评分趋势</p>
      </div>

      {history.length === 0 ? (
        <p className="text-xs text-slate-400 text-center py-12">暂无学习记录</p>
      ) : (
        <>
          {/* Desktop: table */}
          <div className="hidden sm:block rounded-xl border border-amber-100 bg-white shadow-sm overflow-hidden">
            <div className="grid grid-cols-[100px_1fr_60px_80px_80px] gap-4 px-5 py-3 border-b border-amber-100 text-xs text-slate-400 font-medium">
              <span>日期</span>
              <span>视频名称</span>
              <span className="text-center">已练</span>
              <span className="text-center">总句</span>
              <span className="text-center">均分</span>
            </div>
            {history.map((h, i) => (
              <div
                key={i}
                onClick={() => h.practiced > 0 && onStartPractice(h.video_id, h.video)}
                className={`grid grid-cols-[100px_1fr_60px_80px_80px] gap-4 px-5 py-3.5 items-center transition-colors duration-150 ${
                  i === 0 ? 'bg-coral/[0.03]' : ''
                } hover:bg-amber-50 border-b border-amber-50 last:border-0 ${h.practiced > 0 ? 'cursor-pointer' : ''}`}
              >
                <span className="text-sm text-slate-500">{h.date}</span>
                <span className="text-sm text-slate-700 truncate">{h.video}</span>
                <span className="text-sm text-slate-400 text-center">{h.practiced}</span>
                <span className="text-sm text-slate-400 text-center">{h.sentences}</span>
                <div className="flex justify-center">
                  <span className={`text-xs font-semibold px-3 py-1 rounded-full border ${h.avg_score > 0 ? medalDisplay(h.avg_score).cls : 'text-slate-300 bg-slate-50 border-slate-200'}`}>
                    {h.avg_score > 0 ? `${medalDisplay(h.avg_score).emoji} ${medalDisplay(h.avg_score).text}` : '-'}
                  </span>
                </div>
              </div>
            ))}
          </div>

          {/* Mobile: card list */}
          <div className="sm:hidden space-y-3">
            {history.map((h, i) => (
              <div
                key={i}
                onClick={() => h.practiced > 0 && onStartPractice(h.video_id, h.video)}
                className={`rounded-xl border px-4 py-3.5 bg-white shadow-sm ${
                  i === 0 ? 'border-coral/30' : 'border-amber-100'
                } ${h.practiced > 0 ? 'cursor-pointer' : ''}`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs text-slate-400">{h.date}</span>
                  <span className={`text-xs font-semibold px-2.5 py-0.5 rounded-full border ${h.avg_score > 0 ? medalDisplay(h.avg_score).cls : 'text-slate-300 bg-slate-50 border-slate-200'}`}>
                    {h.avg_score > 0 ? `${medalDisplay(h.avg_score).emoji} ${medalDisplay(h.avg_score).text}` : '-'}
                  </span>
                </div>
                <p className="text-sm text-slate-700 font-medium truncate">{h.video}</p>
                <div className="flex items-center gap-3 mt-2 text-[11px] text-slate-400">
                  <span>练习: {h.practiced}/{h.sentences} 句</span>
                  <span>·</span>
                  <span className={h.avg_score >= 80 ? 'text-emerald-600 font-medium' : h.avg_score >= 60 ? 'text-amber-600 font-medium' : 'text-rose-600 font-medium'}>
                    {h.avg_score >= 80 ? '优秀' : h.avg_score >= 60 ? '良好' : h.practiced > 0 ? '继续加油' : '未练习'}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  )
}

// ── App ────────────────────────────────────────────────────────────────────

export default function App() {
  const [tab, setTab] = useState<Tab>('practice')
  const [videos, setVideos] = useState<VideoInfo[]>([])
  const [history, setHistory] = useState<HistoryItem[]>([])
  const [selectedVideoId, setSelectedVideoId] = useState<string | null>(null)
  const [selectedVideoName, setSelectedVideoName] = useState('')

  const fetchVideos = useCallback(() => {
    api<{videos: VideoInfo[]}>('/api/videos')
      .then(data => setVideos(data.videos))
      .catch(() => {})
  }, [])

  const fetchHistory = useCallback(() => {
    api<{history: HistoryItem[]}>('/api/history')
      .then(data => setHistory(data.history))
      .catch(() => {})
  }, [])

  useEffect(() => {
    fetchVideos()
    fetchHistory()
  }, [fetchVideos, fetchHistory])

  const handleStartPractice = (id: string, name: string) => {
    setSelectedVideoId(id)
    setSelectedVideoName(name)
    setTab('practice')
  }

  return (
    <div className="min-h-screen">
      <Navbar active={tab} onTabChange={setTab} />
      {tab === 'import' && (
        <ImportPage
          videos={videos}
          onVideosChange={() => { fetchVideos(); fetchHistory() }}
          onStartPractice={handleStartPractice}
        />
      )}
      {tab === 'practice' && (
        <PracticePage
          selectedVideoId={selectedVideoId}
          selectedVideoName={selectedVideoName}
          onBackToImport={() => setTab('import')}
        />
      )}
      {tab === 'history' && <HistoryPage history={history} onStartPractice={handleStartPractice} />}
    </div>
  )
}
