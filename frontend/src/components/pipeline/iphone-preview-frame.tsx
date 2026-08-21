"use client";

import * as React from "react";

export function IphonePreviewFrame({ children, bottomBar }: { children: React.ReactNode; bottomBar?: React.ReactNode }) {
  return (
    <div className="relative mx-auto aspect-[390/844] w-full max-w-[390px] rounded-[54px] border-[9px] border-[#171717] bg-[#171717] p-[3px] shadow-[0_24px_70px_rgba(0,0,0,0.28)]">
      <span className="absolute -left-[12px] top-[116px] h-8 w-[3px] rounded-l bg-[#242424]" />
      <span className="absolute -left-[12px] top-[164px] h-14 w-[3px] rounded-l bg-[#242424]" />
      <span className="absolute -right-[12px] top-[148px] h-20 w-[3px] rounded-r bg-[#242424]" />
      <div className="absolute inset-[3px] overflow-hidden rounded-[41px] bg-[#f5f5f5] font-sans text-neutral-900">
        <div className="absolute inset-x-0 top-0 z-30 flex h-8 items-center justify-between bg-white px-5 text-[9px] font-semibold"><span>9:41</span><span className="pr-1">●●● &nbsp; Wi-Fi &nbsp; ▰</span></div>
        <div className="absolute left-1/2 top-2 z-40 h-[18px] w-[88px] -translate-x-1/2 rounded-full bg-black" />
        <div className={`absolute inset-x-0 top-8 overflow-y-auto overscroll-contain [scrollbar-width:none] [&::-webkit-scrollbar]:hidden ${bottomBar ? "bottom-16" : "bottom-0"}`}>{children}</div>
        {bottomBar ? <div className="absolute inset-x-0 bottom-0 z-30 h-16 border-t border-neutral-200 bg-white">{bottomBar}</div> : null}
        <div className="absolute bottom-1 left-1/2 z-40 h-1 w-28 -translate-x-1/2 rounded-full bg-black/80" />
      </div>
    </div>
  );
}
