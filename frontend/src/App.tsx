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
  sentences: number
  score: number
}

interface VideoInfo {
  id: string
  name: string
  duration: string
  status: string
}

interface ProcessResult {
  video_id: string
  sentences: Sentence[]
}

interface ScoreResult {
  pronunciation: number
  fluency: number
  timing: number
  overall: number
}

// ── API ────────────────────────────────────────────────────────────────────

async function api<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init)
  if (!res.ok) throw new Error(`${res.status}: ${res.statusText}`)
  return res.json()
}

// ── Helpers ────────────────────────────────────────────────────────────────

const SCORE_STYLES = {
  high: 'text-emerald-600 bg-emerald-50 border-emerald-200',
  mid: 'text-amber-600 bg-amber-50 border-amber-200',
  low: 'text-rose-600 bg-rose-50 border-rose-200',
} as const

function scoreBadge(score: number) {
  if (score >= 80) return SCORE_STYLES.high
  if (score >= 60) return SCORE_STYLES.mid
  return SCORE_STYLES.low
}

// ── Score Ring Component ───────────────────────────────────────────────────

function ScoreRing({ pct, label, color }: { pct: number; label: string; color: string }) {
  const r = 34
  const c = 2 * Math.PI * r
  const offset = c * (1 - pct / 100)
  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative w-24 h-24">
        <svg className="w-24 h-24 -rotate-90" viewBox="0 0 80 80">
          <circle cx="40" cy="40" r={r} fill="none" stroke="#f1e9dd" strokeWidth="5" />
          <circle
            cx="40" cy="40" r={r}
            fill="none" stroke={color} strokeWidth="5"
            strokeLinecap="round"
            strokeDasharray={c}
            strokeDashoffset={offset}
            className="transition-all duration-1000 ease-out"
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-xl font-bold" style={{ color }}>{pct}%</span>
        </div>
      </div>
      <span className="text-sm text-slate-500">{label}</span>
    </div>
  )
}

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
          <span className="text-slate-600 hidden sm:inline">AfterMe</span>
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
  const [dragOver, setDragOver] = useState(false)
  const fileRef = useRef<HTMLInputElement>(null)

  const doUpload = useCallback(async (file: File) => {
    if (!file.name.match(/\.(mp4|avi|mov|mkv|webm)$/i)) {
      alert('不支持的文件格式。支持: mp4, avi, mov, mkv, webm')
      return
    }
    setUploading(true)
    try {
      const form = new FormData()
      form.append('file', file)
      const result = await api<ProcessResult>('/api/upload', { method: 'POST', body: form })
      onVideosChange()
      if (result.video_id) {
        onStartPractice(result.video_id, file.name)
      }
    } catch (e: any) {
      alert('上传失败: ' + (e.message || '未知错误'))
    } finally {
      setUploading(false)
    }
  }, [onVideosChange, onStartPractice])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)
    const file = e.dataTransfer.files[0]
    if (file) doUpload(file)
  }, [doUpload])

  return (
    <div className="animate-enter max-w-3xl mx-auto px-4 md:px-8 py-4 md:py-8 space-y-6 md:space-y-8">
      <div>
        <h1 className="text-xl md:text-2xl font-bold text-slate-700">导入视频</h1>
        <p className="text-xs md:text-sm text-slate-400 mt-1">上传英语视频，自动生成跟读句子</p>
      </div>

      {/* Upload zone */}
      <div
        onClick={() => fileRef.current?.click()}
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
            <p className="text-sm text-slate-500">正在上传和处理视频...</p>
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
  const [scores, setScores] = useState<ScoreResult | null>(null)
  const [recording, setRecording] = useState(false)
  const mediaRecorder = useRef<MediaRecorder | null>(null)
  const audioChunks = useRef<Blob[]>([])
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const [recordedBlob, setRecordedBlob] = useState<Blob | null>(null)
  const [recordingDuration, setRecordingDuration] = useState(0)
  const recTimer = useRef<ReturnType<typeof setInterval> | null>(null)
  const videoRef = useRef<HTMLVideoElement | null>(null)
  const [playing, setPlaying] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)

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
      setScores(null)
      setRecordedBlob(null)
      setCurrentTime(0)
    }).catch(() => {
      setSentences([])
    }).finally(() => setLoading(false))
  }, [selectedVideoId])

  // Auto-highlight + pause at end of current sentence
  const onTimeUpdate = () => {
    if (!videoRef.current || sentences.length === 0) return
    const t = videoRef.current.currentTime
    setCurrentTime(t)

    // Pause when current sentence finishes (user can replay easily)
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
    setScores(null)
    setRecordedBlob(null)
    videoRef.current.currentTime = sentences[idx].start
    videoRef.current.play()
    setPlaying(true)
  }

  // Start recording
  const startRecording = async () => {
    try {
      // Check for secure context requirement
      if (window.location.protocol !== 'https:' && window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
        const ok = confirm('录音需要 HTTPS 连接。Android 浏览器通过 LAN IP 访问时可能会被阻止。\n\n推荐方案:\n1. 使用 Chrome 浏览器\n2. 通过 USB 调试 (adb reverse tcp:9005 tcp:9005)\n3. 或者继续尝试 (可能失败)\n\n是否继续尝试？')
        if (!ok) return
      }

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })

      // Pick best supported MIME type for MediaRecorder
      const mimeTypes = ['audio/webm;codecs=opus', 'audio/webm', 'audio/ogg;codecs=opus', '']
      const mrType = mimeTypes.find(t => MediaRecorder.isTypeSupported(t)) || ''
      const mr = new MediaRecorder(stream, mrType ? { mimeType: mrType } : undefined)
      mediaRecorder.current = mr
      audioChunks.current = []
      setRecordedBlob(null)
      setScores(null)

      mr.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunks.current.push(e.data)
      }

      mr.onstop = () => {
        stream.getTracks().forEach(t => t.stop())
        const blob = new Blob(audioChunks.current, { type: mrType || 'audio/webm' })
        setRecordedBlob(blob)
        setRecordingDuration(0)
        if (audioRef.current) {
          audioRef.current.src = URL.createObjectURL(blob)
        }
      }

      mr.start()
      setRecording(true)
      const startTime = Date.now()
      recTimer.current = setInterval(() => {
        setRecordingDuration(Math.floor((Date.now() - startTime) / 1000))
      }, 200)
    } catch (e: any) {
      const msg = e?.name || e?.message || '未知错误'
      if (msg === 'NotAllowedError') {
        alert('麦克风权限被拒绝，请在浏览器设置中允许麦克风访问')
      } else if (msg === 'NotFoundError') {
        alert('未找到麦克风设备，请确保已连接麦克风')
      } else if (msg.includes('Secure') || msg.includes('secure')) {
        alert('录音需要 HTTPS 连接，当前页面不是安全连接。请用 Chrome 浏览器打开。')
      } else {
        alert('无法访问麦克风: ' + msg)
      }
    }
  }

  const stopRecording = () => {
    mediaRecorder.current?.stop()
    setRecording(false)
    if (recTimer.current) clearInterval(recTimer.current)
  }

  const playRecording = () => {
    audioRef.current?.play()
  }

  const submitScoring = async () => {
    if (!recordedBlob || !selectedVideoId) return
    setScoring(true)
    try {
      const form = new FormData()
      form.append('video_id', selectedVideoId)
      form.append('sentence_index', String(activeIdx))
      form.append('file', recordedBlob, `recording_${activeIdx}.webm`)
      const result = await api<ScoreResult>('/api/score', { method: 'POST', body: form })
      setScores(result)
    } catch (e: any) {
      alert('评分失败: ' + (e.message || '未知错误'))
    } finally {
      setScoring(false)
    }
  }

  const refDuration = sentences[activeIdx]
    ? sentences[activeIdx].end - sentences[activeIdx].start
    : 0

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
              onPlay={() => setPlaying(true)}
              onPause={() => setPlaying(false)}
              onLoadedMetadata={() => { if (videoRef.current) videoRef.current.playbackRate = 1 }}
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
              ▶
            </button>
            <audio ref={audioRef} className="hidden" />
            <div className="hidden sm:block flex-1">
              <Waveform />
            </div>
            <div className="sm:hidden flex-1">
              <WaveformBars count={20} />
            </div>
            <span className="text-[10px] md:text-xs text-slate-400 tabular-nums shrink-0">
              {recording ? `00:${recordingDuration.toString().padStart(2, '0')}` : '00:00 / 00:00'}
            </span>
            {recordedBlob && !scoring && !scores && (
              <button
                onClick={submitScoring}
                className="text-xs font-medium px-3 py-1.5 rounded-lg bg-coral/10 text-coral-dark hover:bg-coral/20 transition shrink-0"
              >
                评分
              </button>
            )}
            {scoring && (
              <div className="w-5 h-5 border-2 border-coral/30 border-t-coral rounded-full animate-spin shrink-0" />
            )}
          </div>

          {/* Score Display */}
          {scores && (
            <div className="rounded-xl border border-amber-100 bg-white shadow-sm p-4 md:p-6">
              <div className="flex items-center justify-between mb-4 md:mb-6">
                <h3 className="text-sm md:text-base font-semibold text-slate-700">📈 评分概览</h3>
                <div className="flex items-baseline gap-1.5">
                  <span className="text-2xl md:text-3xl font-bold text-coral-dark">{scores.overall}</span>
                  <span className="text-xs md:text-sm text-slate-400">/ 100</span>
                </div>
              </div>
              <div className="flex items-center justify-center gap-6 sm:gap-10 md:gap-16 flex-wrap">
                <ScoreRing pct={scores.pronunciation} label="发音准确度" color="#fb7185" />
                <ScoreRing pct={scores.fluency} label="流利度" color="#fbbf24" />
                <ScoreRing pct={scores.timing} label="节奏匹配" color="#34d399" />
              </div>
            </div>
          )}
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
                    className={`px-3 md:px-4 py-2.5 md:py-3 rounded-lg cursor-pointer transition-all duration-200 border ${
                      i === activeIdx
                        ? 'bg-coral/[0.06] border-coral/30 shadow-sm'
                        : 'bg-white border-transparent hover:bg-amber-50 hover:border-amber-200'
                    }`}
                  >
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
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

// ── History Page ───────────────────────────────────────────────────────────

function HistoryPage({ history }: { history: HistoryItem[] }) {
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
            <div className="grid grid-cols-[100px_1fr_70px_80px] gap-4 px-5 py-3 border-b border-amber-100 text-xs text-slate-400 font-medium">
              <span>日期</span>
              <span>视频名称</span>
              <span className="text-center">句子数</span>
              <span className="text-center">评分</span>
            </div>
            {history.map((h, i) => (
              <div
                key={i}
                className={`grid grid-cols-[100px_1fr_70px_80px] gap-4 px-5 py-3.5 items-center transition-colors duration-150 ${
                  i === 0 ? 'bg-coral/[0.03]' : ''
                } hover:bg-amber-50 border-b border-amber-50 last:border-0 cursor-pointer`}
              >
                <span className="text-sm text-slate-500">{h.date}</span>
                <span className="text-sm text-slate-700">{h.video}</span>
                <span className="text-sm text-slate-400 text-center">{h.sentences}</span>
                <div className="flex justify-center">
                  <span className={`text-xs font-semibold px-3 py-1 rounded-full border ${scoreBadge(h.score)}`}>
                    {h.score}
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
                className={`rounded-xl border px-4 py-3.5 bg-white shadow-sm ${
                  i === 0 ? 'border-coral/30' : 'border-amber-100'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs text-slate-400">{h.date}</span>
                  <span className={`text-xs font-semibold px-2.5 py-0.5 rounded-full border ${scoreBadge(h.score)}`}>
                    {h.score} 分
                  </span>
                </div>
                <p className="text-sm text-slate-700 font-medium truncate">{h.video}</p>
                <div className="flex items-center gap-3 mt-2 text-[11px] text-slate-400">
                  <span>句子: {h.sentences}</span>
                  <span>·</span>
                  <span className={h.score >= 80 ? 'text-emerald-600 font-medium' : h.score >= 60 ? 'text-amber-600 font-medium' : 'text-rose-600 font-medium'}>
                    {h.score >= 80 ? '优秀' : h.score >= 60 ? '良好' : '继续加油'}
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
      {tab === 'history' && <HistoryPage history={history} />}
    </div>
  )
}
