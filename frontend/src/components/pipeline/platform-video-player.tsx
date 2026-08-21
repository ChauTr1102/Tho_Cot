"use client";

import * as React from "react";
import { Bookmark, Heart, Home, Inbox, Maximize, MessageCircle, Music2, Pause, Play, Plus, RotateCcw, Search, Share2, UserRound, Users, Volume2, VolumeX } from "lucide-react";

interface PlatformVideoPlayerProps {
  src: string;
  poster?: string;
  title: string;
  caption?: string;
  platform: "tiktok" | "shopee";
  fit?: "contain" | "cover";
  tiktokChrome?: boolean;
}

function formatTime(seconds: number) {
  if (!Number.isFinite(seconds)) return "0:00";
  const minutes = Math.floor(seconds / 60);
  return `${minutes}:${Math.floor(seconds % 60).toString().padStart(2, "0")}`;
}

export function PlatformVideoPlayer({ src, poster, title, caption, platform, fit = "contain", tiktokChrome = false }: PlatformVideoPlayerProps) {
  const videoRef = React.useRef<HTMLVideoElement>(null);
  const [playing, setPlaying] = React.useState(false);
  const [muted, setMuted] = React.useState(false);
  const [currentTime, setCurrentTime] = React.useState(0);
  const [duration, setDuration] = React.useState(0);
  const [ended, setEnded] = React.useState(false);
  const [error, setError] = React.useState(false);
  const [liked, setLiked] = React.useState(false);
  const [saved, setSaved] = React.useState(false);
  const accent = platform === "tiktok" ? "#fe2c55" : "#ee4d2d";
  const showTiktokUi = platform === "tiktok" && tiktokChrome;

  const togglePlayback = async () => {
    const video = videoRef.current;
    if (!video) return;
    if (video.paused || video.ended) {
      if (video.ended) video.currentTime = 0;
      try {
        await video.play();
        setError(false);
      } catch {
        setError(true);
      }
    } else {
      video.pause();
    }
  };

  const enterFullscreen = async () => {
    const video = videoRef.current;
    if (!video) return;
    if (video.requestFullscreen) await video.requestFullscreen();
  };

  return <div className="group relative h-full w-full overflow-hidden bg-black text-white">
    <video
      ref={videoRef}
      src={src}
      poster={poster}
      autoPlay
      muted={muted}
      playsInline
      preload="metadata"
      aria-label={`Video sản phẩm ${title}`}
      className={`h-full w-full ${fit === "cover" ? "object-cover" : "object-contain"}`}
      onClick={() => void togglePlayback()}
      onPlay={() => { setPlaying(true); setEnded(false); }}
      onPause={() => setPlaying(false)}
      onEnded={() => { setPlaying(false); setEnded(true); }}
      onLoadedMetadata={(event) => setDuration(event.currentTarget.duration || 0)}
      onDurationChange={(event) => setDuration(event.currentTarget.duration || 0)}
      onTimeUpdate={(event) => setCurrentTime(event.currentTarget.currentTime)}
      onError={() => { setPlaying(false); setError(true); }}
    />

    <button type="button" onClick={() => void togglePlayback()} aria-label={playing ? "Tạm dừng video" : "Phát video"} className={`absolute inset-0 z-20 m-auto flex h-14 w-14 items-center justify-center rounded-full shadow-lg transition-all ${playing ? "scale-75 bg-black/0 opacity-0 group-hover:scale-100 group-hover:bg-black/55 group-hover:opacity-100" : "bg-black/60 opacity-100"}`}>
      {ended ? <RotateCcw className="h-6 w-6" /> : playing ? <Pause className="h-6 w-6 fill-white" /> : <Play className="ml-0.5 h-6 w-6 fill-white" />}
    </button>

    {error ? <div className="absolute inset-x-4 top-1/2 -translate-y-1/2 bg-black/75 px-3 py-2 text-center text-[11px]">Không thể phát video. Hãy kiểm tra kết nối tới máy chủ media.</div> : null}

    {showTiktokUi ? <>
      <div className="pointer-events-none absolute inset-x-0 top-0 z-30 flex h-12 items-center justify-center bg-gradient-to-b from-black/55 to-transparent px-4 text-[11px] font-semibold drop-shadow-md">
        <div className="flex items-center gap-5"><span className="text-white/55">Đang Follow</span><span className="relative text-white">Dành cho bạn<span className="absolute -bottom-2 left-1/2 h-0.5 w-5 -translate-x-1/2 rounded-full bg-white" /></span></div>
        <Search className="absolute right-4 h-5 w-5 text-white" />
      </div>
      <div className="absolute bottom-20 right-2.5 z-30 flex flex-col items-center gap-2.5 text-white drop-shadow-[0_1px_3px_rgba(0,0,0,0.8)]">
        <div className="relative mb-1 flex h-10 w-10 items-center justify-center rounded-full border-2 border-white bg-neutral-800 text-xs font-bold">{title.trim().charAt(0).toUpperCase() || "P"}<span className="absolute -bottom-1 flex h-4 w-4 items-center justify-center rounded-full bg-[#fe2c55]"><Plus className="h-3 w-3 stroke-[3]" /></span></div>
        <button type="button" onClick={() => setLiked((value) => !value)} aria-label={liked ? "Bỏ thích" : "Thích video"} aria-pressed={liked} className="flex h-9 w-9 items-center justify-center rounded-full bg-black/25 transition-transform hover:scale-105"><Heart className={`h-6 w-6 ${liked ? "fill-[#fe2c55] text-[#fe2c55]" : "fill-white text-white"}`} /></button>
        <button type="button" aria-label="Xem bình luận" className="flex h-9 w-9 items-center justify-center rounded-full bg-black/25 transition-transform hover:scale-105"><MessageCircle className="h-6 w-6 fill-white text-white" /></button>
        <button type="button" onClick={() => setSaved((value) => !value)} aria-label={saved ? "Bỏ lưu" : "Lưu video"} aria-pressed={saved} className="flex h-9 w-9 items-center justify-center rounded-full bg-black/25 transition-transform hover:scale-105"><Bookmark className={`h-6 w-6 ${saved ? "fill-[#face15] text-[#face15]" : "fill-white text-white"}`} /></button>
        <button type="button" aria-label="Chia sẻ video" className="flex h-9 w-9 items-center justify-center rounded-full bg-black/25 transition-transform hover:scale-105"><Share2 className="h-6 w-6 fill-white text-white" /></button>
        <button type="button" onClick={() => { const video = videoRef.current; if (!video) return; video.muted = !video.muted; setMuted(video.muted); }} aria-label={muted ? "Bật âm thanh" : "Tắt âm thanh"} className="mt-1 flex h-9 w-9 items-center justify-center rounded-full border border-white/30 bg-neutral-900/85"><Music2 className="h-4 w-4 animate-spin [animation-duration:4s]" /></button>
      </div>
      <div className="pointer-events-none absolute inset-x-0 bottom-12 z-20 bg-gradient-to-t from-black/85 to-transparent px-3 pb-3 pr-14 pt-12 text-left text-white">
        <p className="truncate text-[11px] font-bold">@tiktokshop</p>
        <p className="mt-1 line-clamp-3 text-[10px] leading-4">{caption || title}</p>
        <p className="mt-2 flex items-center gap-1.5 truncate text-[9px] text-white/90"><Music2 className="h-3 w-3 shrink-0" /> Âm thanh gốc · TikTok Shop</p>
      </div>
      <nav className="absolute inset-x-0 bottom-0 z-30 grid h-12 grid-cols-5 items-center border-t border-white/10 bg-black px-1 text-[7px] font-medium text-white" aria-label="Điều hướng TikTok">
        <button type="button" className="flex h-full flex-col items-center justify-center gap-0.5"><Home className="h-4 w-4 fill-white" />Trang chủ</button>
        <button type="button" className="flex h-full flex-col items-center justify-center gap-0.5"><Users className="h-4 w-4" />Bạn bè</button>
        <button type="button" aria-label="Tạo video" className="flex h-full items-center justify-center"><span className="flex h-6 w-10 items-center justify-center rounded-md bg-gradient-to-r from-[#25f4ee] via-white to-[#fe2c55] text-black"><Plus className="h-4 w-4 stroke-[3]" /></span></button>
        <button type="button" className="flex h-full flex-col items-center justify-center gap-0.5"><Inbox className="h-4 w-4" />Hộp thư</button>
        <button type="button" className="flex h-full flex-col items-center justify-center gap-0.5"><UserRound className="h-4 w-4" />Hồ sơ</button>
      </nav>
    </> : null}

    {!showTiktokUi ? <div className="absolute inset-x-0 bottom-0 z-10 bg-gradient-to-t from-black/90 via-black/55 to-transparent px-3 pb-2.5 pt-8 opacity-100 transition-opacity sm:opacity-0 sm:group-hover:opacity-100">
      <input
        type="range"
        min={0}
        max={duration || 0}
        step="0.05"
        value={Math.min(currentTime, duration || 0)}
        onChange={(event) => {
          const next = Number(event.target.value);
          if (videoRef.current) videoRef.current.currentTime = next;
          setCurrentTime(next);
        }}
        aria-label="Tiến trình video"
        className="h-1 w-full cursor-pointer appearance-none rounded-full bg-white/35 accent-[var(--video-accent)]"
        style={{ "--video-accent": accent } as React.CSSProperties}
      />
      <div className="mt-2 flex items-center gap-2 text-[10px] font-medium">
        <button type="button" onClick={() => void togglePlayback()} aria-label={playing ? "Tạm dừng" : "Phát"} className="flex h-7 w-7 items-center justify-center rounded-full hover:bg-white/15">{playing ? <Pause className="h-4 w-4 fill-white" /> : <Play className="h-4 w-4 fill-white" />}</button>
        <span className="tabular-nums">{formatTime(currentTime)} / {formatTime(duration)}</span>
        <span className="flex-1" />
        <button type="button" onClick={() => { const video = videoRef.current; if (!video) return; video.muted = !video.muted; setMuted(video.muted); }} aria-label={muted ? "Bật âm thanh" : "Tắt âm thanh"} className="flex h-7 w-7 items-center justify-center rounded-full hover:bg-white/15">{muted ? <VolumeX className="h-4 w-4" /> : <Volume2 className="h-4 w-4" />}</button>
        <button type="button" onClick={() => void enterFullscreen()} aria-label="Toàn màn hình" className="flex h-7 w-7 items-center justify-center rounded-full hover:bg-white/15"><Maximize className="h-4 w-4" /></button>
      </div>
    </div> : null}

    {platform === "shopee" ? <span className="pointer-events-none absolute left-3 top-3 z-10 rounded-sm bg-[#ee4d2d] px-2 py-1 text-[9px] font-bold text-white">Shopee Video</span> : null}
  </div>;
}
