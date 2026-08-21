"use client";

import * as React from "react";
import { AgentLoading } from "./agent-loading";
import { 
  Check, Target, User, History, ExternalLink, BarChart3, TrendingUp, Sparkles, AlertTriangle, Globe, LineChart as LineChartIcon, Link2, ShieldCheck, BarChart2
} from "lucide-react";
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, LineChart, Line, PieChart, Pie, Cell } from "recharts";

// Mock Data cho G7
const productData = [
  { subject: 'Vị đậm Việt', value: 95, fullMark: 100 },
  { subject: 'Tiện lợi 3in1', value: 90, fullMark: 100 },
  { subject: 'Thương hiệu', value: 85, fullMark: 100 },
  { subject: 'Thức tỉnh', value: 90, fullMark: 100 },
  { subject: 'Quà tặng', value: 80, fullMark: 100 },
];

const userResearchData = [
  { name: '18-24 (SV)', value: 35 },
  { name: '25-34 (VP)', value: 45 },
  { name: '35-44 (GĐ)', value: 15 },
  { name: 'Khác', value: 5 },
];

const marketTrendData = [
  { name: 'T4', trend: 300 },
  { name: 'T5', trend: 350 },
  { name: 'T6', trend: 450 },
  { name: 'T7', trend: 600 },
  { name: 'T8', trend: 750 },
  { name: 'T9 (Dự kiến)', trend: 950 },
];

const evidenceData = [
  { name: 'Báo cáo ngành (ChinaIRN, 21Jingji)', value: 40 },
  { name: 'Hành vi mua sắm (Tmall, Shopee)', value: 30 },
  { name: 'Mạng xã hội (Douyin, TikTok)', value: 20 },
  { name: 'Brief khách hàng', value: 10 },
];
const COLORS = ['#35ea52', '#22c55e', '#16a34a', '#15803d'];

type Tab = "product" | "user" | "market" | "evidence";

export const StageResearch: React.FC = () => {
  const [isProcessing, setIsProcessing] = React.useState(true);
  const [activeTab, setActiveTab] = React.useState<Tab>("product");

  React.useEffect(() => {
    // Single loading phase that takes slightly longer to simulate 4 phases
    const timer = setTimeout(() => setIsProcessing(false), 4500);
    return () => clearTimeout(timer);
  }, []);

  const steps = [
    "Parsing product metadata & features...",
    "Analyzing target audience demographics...",
    "Scanning market trends & competitor landscape...",
    "Synthesizing evidence and policy compliance..."
  ];

  if (isProcessing) {
    return (
      <div className="h-full flex flex-col justify-center max-w-xl mx-auto w-full">
        <AgentLoading agentName="GLOBAL_RESEARCH_AGENT" steps={steps} isComplete={false} />
      </div>
    );
  }

  return (
    <div className="space-y-6 h-full flex flex-col animate-in fade-in duration-500">
      
      {/* Header */}
      <div className="space-y-4 border-b border-foreground/10 pb-4">
        <h2 className="text-lg font-bold font-mono tracking-wider text-foreground">PHÂN TÍCH & NGHIÊN CỨU</h2>
        <p className="text-sm font-mono text-foreground/40">
          Hệ thống đã thu thập và xử lý toàn bộ dữ liệu. Chọn các phân hệ bên dưới để xem chi tiết.
        </p>

        {/* Tabs */}
        <div className="flex flex-wrap gap-2 pt-2">
          {[
            { id: "product", label: "HIỂU SẢN PHẨM" },
            { id: "user", label: "NGƯỜI DÙNG" },
            { id: "market", label: "THỊ TRƯỜNG" },
            { id: "evidence", label: "BẰNG CHỨNG" },
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as Tab)}
              className={`px-4 py-2 text-xs font-mono font-bold tracking-widest transition-all border ${
                activeTab === tab.id 
                  ? "bg-[#35ea52] text-black border-[#35ea52]" 
                  : "bg-transparent text-foreground/50 border-foreground/10 hover:border-foreground/30 hover:text-foreground"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto">
        {/* --- PRODUCT TAB --- */}
        {activeTab === "product" && (
          <div className="flex flex-col gap-6 animate-in fade-in slide-in-from-bottom-2 duration-300">
            {/* Chart Section */}
            <div className="flex flex-col md:flex-row gap-8 p-6 border border-foreground/10 bg-foreground/[0.02]">
              <div className="flex-1 flex flex-col justify-center space-y-4">
                <div className="flex items-center gap-2">
                  <Target className="h-4 w-4 text-[#35ea52]" />
                  <h3 className="text-sm font-mono font-bold text-foreground tracking-widest uppercase">Phân Tích Đa Chiều (G7)</h3>
                </div>
                <p className="text-sm font-mono text-foreground/60 leading-relaxed max-w-xl">
                  Sản phẩm nổi bật với <strong className="text-foreground">Vị đậm đặc trưng (95/100)</strong> từ cà phê Robusta Buôn Ma Thuột, kết hợp với tính <strong className="text-foreground">Tiện lợi 3in1 (90/100)</strong>.
                  <br /><br />
                  Đây là yếu tố then chốt tạo nên lợi thế cạnh tranh cốt lõi của G7 so với các thương hiệu toàn cầu, phù hợp với nhu cầu khởi đầu ngày mới bứt tốc.
                </p>
              </div>
              <div className="h-[280px] w-full md:w-[320px] lg:w-[400px] shrink-0">
                <ResponsiveContainer width="100%" height="100%">
                  <RadarChart cx="50%" cy="50%" outerRadius="70%" data={productData}>
                    <PolarGrid stroke="#333" />
                    <PolarAngleAxis dataKey="subject" tick={{ fill: '#888', fontSize: 11 }} />
                    <Radar name="Đánh giá" dataKey="value" stroke="#35ea52" fill="#35ea52" fillOpacity={0.2} />
                    <Tooltip contentStyle={{ backgroundColor: '#000', border: '1px solid #333' }} itemStyle={{ color: '#35ea52' }} />
                  </RadarChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="flex flex-col lg:flex-row gap-6">
              {/* Extracted Features */}
              <div className="flex-1 border border-foreground/10 bg-foreground/[0.02] p-6 space-y-4">
                <h3 className="text-xs font-mono text-foreground/50 uppercase tracking-widest">Tính năng được trích xuất</h3>
                <ul className="space-y-3 text-sm font-mono">
                  <li className="flex items-start gap-3">
                    <Check className="h-4 w-4 text-[#35ea52] shrink-0 mt-0.5" />
                    <span className="text-foreground/80">Robusta Buôn Ma Thuột, đậm mạnh, ít chua</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <Check className="h-4 w-4 text-[#35ea52] shrink-0 mt-0.5" />
                    <span className="text-foreground/80">Công thức 3in1 (cà phê, đường, kem) pha nhanh, tiện mang theo</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <Check className="h-4 w-4 text-[#35ea52] shrink-0 mt-0.5" />
                    <span className="text-foreground/80">Thương hiệu Việt Nam xuất khẩu trên 100 quốc gia</span>
                  </li>
                </ul>
              </div>

              {/* Positioning Analysis */}
              <div className="flex-1 border border-foreground/10 bg-foreground/[0.02] p-6 space-y-4">
                <h3 className="text-xs font-mono text-foreground/50 uppercase tracking-widest">Phân tích định vị</h3>
                <div className="space-y-4">
                  <div>
                    <span className="text-[11px] text-foreground/40 block mb-1.5 uppercase tracking-widest">Mức giá</span>
                    <span className="text-sm font-mono text-foreground border border-foreground/20 px-3 py-1 bg-foreground/5">PHỔ THÔNG (Bình dân, dễ tiếp cận)</span>
                  </div>
                  <div>
                    <span className="text-[11px] text-foreground/40 block mb-1.5 uppercase tracking-widest">Phong cách hiện tại</span>
                    <span className="text-sm font-mono text-foreground/80 block">Trẻ trung, năng lượng, tự hào Việt Nam</span>
                  </div>
                </div>
              </div>
            </div>

            {/* USP Analysis */}
            <div className="border border-foreground/10 bg-foreground/[0.02] p-6 space-y-4">
              <h3 className="text-xs font-mono text-foreground/50 uppercase tracking-widest">Ma trận sức mạnh USP</h3>
              <div className="flex flex-wrap gap-4">
                {[
                  { label: "Vị đậm Việt đúng gu", strength: "CAO" },
                  { label: "Tiện lợi 3 trong 1", strength: "CAO" },
                  { label: "Thương hiệu quốc tế", strength: "TRUNG BÌNH" }
                ].map((usp, i) => (
                  <div key={i} className="flex-1 min-w-[200px] border border-foreground/10 p-4 hover:border-foreground/20 transition-colors bg-background/50">
                    <div className="flex justify-between items-center mb-3">
                      <span className={`text-[11px] font-mono font-bold tracking-widest ${usp.strength === 'CAO' ? 'text-[#35ea52]' : 'text-foreground/40'}`}>
                        MỨC ĐỘ: {usp.strength}
                      </span>
                    </div>
                    <p className="text-base font-mono text-foreground">{usp.label}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* --- USER TAB --- */}
        {activeTab === "user" && (
          <div className="flex flex-col gap-6 animate-in fade-in slide-in-from-bottom-2 duration-300">
            {/* Chart Section */}
            <div className="flex flex-col lg:flex-row gap-8 p-6 border border-foreground/10 bg-foreground/[0.02]">
              <div className="flex-1 flex flex-col justify-center space-y-4">
                <div className="flex items-center gap-2">
                  <BarChart3 className="h-4 w-4 text-[#35ea52]" />
                  <h3 className="text-sm font-mono font-bold text-foreground tracking-widest uppercase">Phân Bố Độ Tuổi & Nghề Nghiệp</h3>
                </div>
                <p className="text-sm font-mono text-foreground/60 leading-relaxed max-w-xl">
                  Dân văn phòng (25-34 tuổi) chiếm ưu thế lớn <strong className="text-foreground">(45%)</strong>, theo sau là Sinh viên (18-24) <strong className="text-foreground">(35%)</strong>.
                  <br /><br />
                  Nhóm khách hàng này có lối sống nhanh, cần cà phê để duy trì sự tỉnh táo và tập trung, do đó, sự "tiện lợi" của dòng 3in1 là giải pháp hoàn hảo. Đồng thời, có một lượng lớn khách mua với mục đích làm "quà đặc sản".
                </p>
              </div>
              <div className="h-[280px] w-full lg:w-[500px] shrink-0">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={userResearchData} margin={{ top: 20, right: 30, left: -20, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#333" vertical={false} />
                    <XAxis dataKey="name" stroke="#555" tick={{ fill: '#888', fontSize: 11 }} />
                    <YAxis stroke="#555" tick={{ fill: '#888', fontSize: 11 }} />
                    <Tooltip cursor={{ fill: '#35ea52', opacity: 0.1 }} contentStyle={{ backgroundColor: '#000', border: '1px solid #333' }} itemStyle={{ color: '#35ea52' }} />
                    <Bar dataKey="value" fill="#35ea52" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Past Campaigns */}
            <div className="border border-foreground/10 bg-foreground/[0.02] p-6 space-y-5">
              <div className="flex items-center gap-2 text-xs font-mono text-foreground/50 uppercase tracking-widest border-b border-foreground/10 pb-3">
                <History className="h-4 w-4" />
                <span>Lịch sử hành vi trên nền tảng (Douyin / Shopee)</span>
              </div>
              <div className="flex flex-wrap gap-4">
                {[
                  { name: "Cà phê quà tặng 50 gói", date: "Tết 2024", perf: "Doanh thu đột biến", platform: "Tmall", icon: TrendingUp },
                  { name: "Video pha cà phê văn phòng", date: "Q2 2024", perf: "Tỷ lệ chốt đơn cao", platform: "Douyin", icon: Sparkles }
                ].map((camp, i) => (
                  <div key={i} className="flex-1 min-w-[300px] border border-foreground/10 bg-background/50 p-5 space-y-3 hover:border-[#35ea52]/50 transition-colors">
                    <div className="flex justify-between items-start">
                      <span className="text-base font-mono font-bold text-foreground">{camp.name}</span>
                      <span className="text-xs font-mono text-foreground/40 bg-foreground/5 px-2 py-1">{camp.date}</span>
                    </div>
                    <div className="flex justify-between items-center text-sm font-mono pt-2 border-t border-foreground/10">
                      <span className="text-foreground/60">{camp.platform}</span>
                      <span className="text-[#35ea52] flex items-center gap-1.5">
                        <camp.icon className="h-3.5 w-3.5" />
                        {camp.perf}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="flex flex-col lg:flex-row gap-6">
              {/* Visual Preferences */}
              <div className="flex-[2] border border-foreground/10 bg-foreground/[0.02] p-6 space-y-5">
                <div className="flex items-center gap-2 text-xs font-mono text-foreground/50 uppercase tracking-widest border-b border-foreground/10 pb-3">
                  <User className="h-4 w-4" />
                  <span>Sở thích hình ảnh (Dữ liệu học được)</span>
                </div>
                <ul className="space-y-4 text-sm font-mono text-foreground/80">
                  <li className="flex items-start gap-3">
                    <span className="text-[#35ea52] mt-0.5 text-lg leading-none">›</span>
                    <span>Thích cảnh quay cận (macro) rót nước sôi pha cà phê tỏa khói.</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <span className="text-[#35ea52] mt-0.5 text-lg leading-none">›</span>
                    <span>Tương tác tốt với nội dung đánh trúng nỗi đau mệt mỏi, uể oải buổi sáng.</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <span className="text-[#35ea52] mt-0.5 text-lg leading-none">›</span>
                    <span>Giữ thiết kế bao bì gốc đỏ-đen-vàng đồng truyền thống, không biến tấu làm mất nhận diện.</span>
                  </li>
                </ul>
              </div>

              {/* Evidence Link */}
              <div className="flex-1 border border-dashed border-foreground/20 p-6 flex flex-col justify-center items-center text-center space-y-4 bg-background/30 hover:bg-foreground/[0.02] transition-colors">
                <div className="p-3 bg-foreground/5 rounded-full mb-2">
                  <ExternalLink className="h-6 w-6 text-foreground/50" />
                </div>
                <span className="text-sm font-mono text-foreground/60">Được suy ra từ hành vi của 10k users Trung Quốc/Quốc tế</span>
                <button className="flex items-center gap-2 px-5 py-2.5 bg-foreground text-background font-bold text-xs font-mono transition-transform hover:scale-105">
                  XEM BÁO CÁO
                </button>
              </div>
            </div>
          </div>
        )}

        {/* --- MARKET TAB --- */}
        {activeTab === "market" && (
          <div className="flex flex-col gap-6 animate-in fade-in slide-in-from-bottom-2 duration-300">
            {/* Chart Section */}
            <div className="flex flex-col lg:flex-row gap-8 p-6 border border-foreground/10 bg-foreground/[0.02]">
              <div className="flex-1 flex flex-col justify-center space-y-4">
                <div className="flex items-center gap-2">
                  <LineChartIcon className="h-4 w-4 text-[#35ea52]" />
                  <h3 className="text-sm font-mono font-bold text-foreground tracking-widest uppercase">Dự kiến bùng nổ T9 (China 9.9)</h3>
                </div>
                <p className="text-sm font-mono text-foreground/60 leading-relaxed max-w-xl">
                  Lượng tìm kiếm và mua sắm dự kiến sẽ đạt đỉnh vào tháng 9 với sự kiện <strong className="text-foreground">China 9.9 Shopping Festival</strong>.
                  <br /><br />
                  Các sàn như Tmall, JD, Douyin đang tích cực đẩy khuyến mãi. Đây là thời cơ vàng để ra mắt chiến dịch cross-border (mua 3 tặng 1).
                </p>
              </div>
              <div className="h-[280px] w-full lg:w-[500px] shrink-0">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={marketTrendData} margin={{ top: 20, right: 30, left: -20, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#333" vertical={false} />
                    <XAxis dataKey="name" stroke="#555" tick={{ fill: '#888', fontSize: 11 }} />
                    <YAxis stroke="#555" tick={{ fill: '#888', fontSize: 11 }} />
                    <Tooltip cursor={{ stroke: '#35ea52', strokeWidth: 1, strokeDasharray: '3 3' }} contentStyle={{ backgroundColor: '#000', border: '1px solid #333' }} itemStyle={{ color: '#35ea52' }} />
                    <Line type="monotone" dataKey="trend" stroke="#35ea52" strokeWidth={2} dot={{ fill: '#35ea52', r: 4 }} activeDot={{ r: 6 }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
            
            {/* Market Trends */}
            <div className="border border-foreground/10 bg-foreground/[0.02] p-6 space-y-5">
              <div className="flex items-center gap-2 text-xs font-mono text-foreground/50 uppercase tracking-widest border-b border-foreground/10 pb-3">
                <TrendingUp className="h-4 w-4" />
                <span>Góc độ xu hướng (Trends)</span>
              </div>
              <div className="flex flex-wrap gap-4">
                {[
                  { trend: "Livestream Commerce", volume: "CỰC CAO", platform: "Douyin/TikTok" },
                  { trend: "Quà tặng mua số lượng lớn", volume: "ĐANG TĂNG", platform: "Tmall" },
                  { trend: "Lối sống nhanh, tiện lợi", volume: "ỔN ĐỊNH", platform: "Cross-platform" }
                ].map((t, i) => (
                  <div key={i} className="flex-1 min-w-[200px] border border-foreground/10 p-5 bg-background/50 hover:border-[#35ea52]/50 transition-colors">
                    <p className="text-base font-mono font-bold text-foreground mb-3">{t.trend}</p>
                    <div className="flex justify-between items-center text-xs font-mono text-foreground/50 pt-3 border-t border-foreground/10">
                      <span>{t.platform}</span>
                      <span className="text-[#35ea52]">{t.volume}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="flex flex-col lg:flex-row gap-6">
              {/* Competitors */}
              <div className="flex-1 border border-foreground/10 bg-foreground/[0.02] p-6 space-y-5">
                <div className="flex items-center gap-2 text-xs font-mono text-foreground/50 uppercase tracking-widest border-b border-foreground/10 pb-3">
                  <Globe className="h-4 w-4" />
                  <span>Cảnh quan đối thủ / Ngành hàng</span>
                </div>
                <ul className="space-y-4 text-sm font-mono">
                  <li className="border-b border-foreground/5 pb-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-foreground font-bold text-base">Cà phê hòa tan 3in1 nói chung</span>
                    </div>
                    <span className="text-foreground/60 text-xs block mb-1">Dù có xu hướng chuyển dịch sang cà phê đen, 3in1 vẫn là phân khúc lớn nhất.</span>
                    <span className="text-[#35ea52]/80 text-xs flex items-center gap-1.5"><Check className="h-3 w-3" /> Lợi thế G7: Vị đậm, giá rẻ, hợp khẩu vị châu Á.</span>
                  </li>
                  <li>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-foreground font-bold text-base">Các hãng ngoại nhập khác</span>
                    </div>
                    <span className="text-foreground/60 text-xs block mb-1">Cạnh tranh khốc liệt trên các sàn cross-border.</span>
                    <span className="text-red-400/80 text-xs flex items-center gap-1.5"><AlertTriangle className="h-3 w-3" /> Thách thức: Phải nổi bật tính 'đặc sản Việt'.</span>
                  </li>
                </ul>
              </div>

              {/* Policy Warnings */}
              <div className="flex-[0.8] border border-red-500/20 bg-red-500/[0.02] p-6 space-y-5">
                <div className="flex items-center gap-2 text-xs font-mono text-red-400 uppercase tracking-widest border-b border-red-500/20 pb-3">
                  <AlertTriangle className="h-4 w-4" />
                  <span>Quy định bắt buộc (Audit Risk)</span>
                </div>
                <ul className="space-y-4 text-sm font-mono text-foreground/80">
                  <li className="flex items-start gap-3 p-3 bg-red-500/5 border border-red-500/10">
                    <span className="text-red-400 mt-0.5 font-bold">!</span>
                    <span>Cấm so sánh trực tiếp với đối thủ cạnh tranh.</span>
                  </li>
                  <li className="flex items-start gap-3 p-3 bg-red-500/5 border border-red-500/10">
                    <span className="text-red-400 mt-0.5 font-bold">!</span>
                    <span>Không được claim "trị liệu" hay "sức khỏe tuyệt đối" vô căn cứ.</span>
                  </li>
                  <li className="flex items-start gap-3 p-3 bg-red-500/5 border border-red-500/10">
                    <span className="text-red-400 mt-0.5 font-bold">!</span>
                    <span>Tránh sử dụng từ ngữ Superlative (Tốt nhất thế giới...).</span>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        )}

        {/* --- EVIDENCE TAB --- */}
        {activeTab === "evidence" && (
          <div className="flex flex-col gap-6 animate-in fade-in slide-in-from-bottom-2 duration-300">
            {/* Chart Section */}
            <div className="flex flex-col lg:flex-row gap-8 p-6 border border-foreground/10 bg-foreground/[0.02]">
              <div className="flex-1 flex flex-col justify-center space-y-4">
                <div className="flex items-center gap-2">
                  <BarChart2 className="h-4 w-4 text-[#35ea52]" />
                  <h3 className="text-sm font-mono font-bold text-foreground tracking-widest uppercase">Phân bố Nguồn Dữ Liệu G7</h3>
                </div>
                <p className="text-sm font-mono text-foreground/60 leading-relaxed max-w-xl">
                  Dữ liệu được trích xuất từ báo cáo uy tín như <strong className="text-foreground">21 Jingji, ChinaIRN</strong> (40%), kết hợp phân tích hành vi trực tiếp từ các sàn TMĐT quốc tế. Điều này đảm bảo quyết định về định vị bám sát thực tế thị trường.
                </p>
                <div className="flex flex-wrap gap-4 mt-2">
                  {evidenceData.map((entry, index) => (
                    <div key={index} className="flex items-center gap-2 text-[11px] font-mono text-foreground/50 bg-background/50 px-3 py-1.5 border border-foreground/5">
                      <div className="w-2 h-2 rounded-full" style={{ backgroundColor: COLORS[index % COLORS.length] }} />
                      {entry.name}: <span className="text-foreground font-bold">{entry.value}%</span>
                    </div>
                  ))}
                </div>
              </div>
              <div className="h-[280px] w-full lg:w-[400px] shrink-0">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={evidenceData} cx="50%" cy="50%" innerRadius={70} outerRadius={100} paddingAngle={5} dataKey="value" stroke="none">
                      {evidenceData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip contentStyle={{ backgroundColor: '#000', border: '1px solid #333' }} itemStyle={{ color: '#35ea52' }} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Evidence Table */}
            <div className="border border-foreground/10 bg-background">
              {/* Table Header */}
              <div className="grid grid-cols-12 gap-4 p-4 border-b border-foreground/10 text-[11px] font-mono text-foreground/40 uppercase tracking-widest bg-foreground/[0.02]">
                <div className="col-span-12 md:col-span-3">Phát hiện</div>
                <div className="col-span-12 md:col-span-4">Bằng chứng & Suy luận</div>
                <div className="col-span-12 md:col-span-3">Nguồn</div>
                <div className="col-span-12 md:col-span-2 md:text-right">Độ tin cậy</div>
              </div>

              {/* Table Body */}
              <div className="divide-y divide-foreground/10">
                {[
                  { finding: "Người tiêu dùng chuộng 3in1 do tiện lợi", evidence: "Dù thị trường có chuyển dịch, 3in1 vẫn là phân khúc lớn nhất nhờ tính tiện lợi, phù hợp lối sống nhanh.", source: "Nông Thôn Việt", conf: "CAO" },
                  { finding: "Lợi thế vị đậm Robusta", evidence: "Robusta Việt Nam có vị đậm, kết hợp sữa/đường hợp khẩu vị châu Á, cạnh tranh tốt.", source: "ChinaIRN Market Report", conf: "CAO" },
                  { finding: "Event 9.9 rất quan trọng", evidence: "China 9.9 Shopping Festival là sự kiện lớn, tiêu dùng săn sale khủng trên Tmall/JD.", source: "21 Jingji", conf: "TRUNG BÌNH" },
                  { finding: "Promotion vi phạm (nếu có)", evidence: "Không được truyền thông 'dùng đủ 50 ngày' hoặc so sánh trực tiếp, không tuyên bố y tế.", source: "Audit Policy Framework", conf: "NGHIÊM TRỌNG" }
                ].map((row, i) => (
                  <div key={i} className="grid grid-cols-12 gap-4 p-4 text-sm font-mono hover:bg-foreground/[0.02] transition-colors">
                    <div className="col-span-12 md:col-span-3 text-foreground font-bold">{row.finding}</div>
                    <div className="col-span-12 md:col-span-4 text-foreground/60 leading-relaxed">{row.evidence}</div>
                    <div className="col-span-12 md:col-span-3 text-foreground/40 flex items-start gap-2">
                      <Link2 className="h-4 w-4 mt-0.5 shrink-0" />
                      <span className="truncate" title={row.source}>{row.source}</span>
                    </div>
                    <div className="col-span-12 md:col-span-2 md:text-right flex items-center md:justify-end">
                      <span className={`px-3 py-1 border text-[11px] font-bold tracking-widest ${
                        row.conf === 'NGHIÊM TRỌNG' ? 'border-red-500/50 text-red-400 bg-red-500/10' :
                        row.conf === 'CAO' ? 'border-[#35ea52]/50 text-[#35ea52] bg-[#35ea52]/10' :
                        'border-foreground/20 text-foreground/50 bg-foreground/5'
                      }`}>
                        {row.conf}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between p-6 border border-[#35ea52]/20 bg-[#35ea52]/[0.02] gap-4">
              <div className="flex items-center gap-4">
                <div className="p-3 rounded-full bg-[#35ea52]/10">
                  <ShieldCheck className="h-6 w-6 text-[#35ea52]" />
                </div>
                <div className="space-y-1">
                  <p className="text-base font-mono text-[#35ea52] font-bold tracking-wider">ĐÃ XÁC MINH 10 NGUỒN DỮ LIỆU</p>
                  <p className="text-sm font-mono text-foreground/60">Dữ liệu hoàn thiện. Sẵn sàng cho Agent Chiến Lược Định Vị.</p>
                </div>
              </div>
            </div>
          </div>
        )}

      </div>
    </div>
  );
};
