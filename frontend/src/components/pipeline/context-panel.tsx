"use client";

import * as React from "react";
import { CampaignStage } from "@/types/campaign";
import { 
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, 
  RadarChart, PolarGrid, PolarAngleAxis, Radar, 
  LineChart, Line, PieChart, Pie, Cell 
} from "recharts";
import { Activity } from "lucide-react";

interface ContextPanelProps {
  currentStage: CampaignStage;
}

// Mock Data for Charts
const productData = [
  { subject: 'Chất lượng', A: 90, fullMark: 100 },
  { subject: 'Giá cả', A: 85, fullMark: 100 },
  { subject: 'Độc đáo', A: 80, fullMark: 100 },
  { subject: 'Thẩm mỹ', A: 95, fullMark: 100 },
  { subject: 'Tính năng', A: 75, fullMark: 100 },
];

const userResearchData = [
  { name: '18-24', value: 45 },
  { name: '25-34', value: 30 },
  { name: '35-44', value: 15 },
  { name: 'Khác', value: 10 },
];

const marketTrendData = [
  { name: 'T1', trend: 400 },
  { name: 'T2', trend: 300 },
  { name: 'T3', trend: 550 },
  { name: 'T4', trend: 450 },
  { name: 'T5', trend: 700 },
  { name: 'T6', trend: 600 },
];

const evidenceData = [
  { name: 'Mạng xã hội', value: 400 },
  { name: 'Đánh giá KH', value: 300 },
  { name: 'Báo cáo', value: 300 },
  { name: 'Khác', value: 200 },
];
const COLORS = ['#35ea52', '#22c55e', '#16a34a', '#15803d'];

export const ContextPanel: React.FC<ContextPanelProps> = ({ currentStage }) => {
  const renderChart = () => {
    switch (currentStage) {
      case "product_input":
        return (
          <div className="h-[250px] w-full mt-4">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart cx="50%" cy="50%" outerRadius="70%" data={productData}>
                <PolarGrid stroke="#333" />
                <PolarAngleAxis dataKey="subject" tick={{ fill: '#888', fontSize: 10 }} />
                <Radar name="Product" dataKey="A" stroke="#35ea52" fill="#35ea52" fillOpacity={0.3} />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        );
      case "research":
        return (
          <div className="h-[250px] w-full mt-4">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={userResearchData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <XAxis dataKey="name" stroke="#555" tick={{ fill: '#888', fontSize: 10 }} />
                <YAxis stroke="#555" tick={{ fill: '#888', fontSize: 10 }} />
                <Tooltip contentStyle={{ backgroundColor: '#000', border: '1px solid #333' }} itemStyle={{ color: '#35ea52' }} />
                <Bar dataKey="value" fill="#35ea52" radius={[2, 2, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        );
      case "content_generation":
        return (
          <div className="h-[250px] w-full mt-4">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={marketTrendData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <XAxis dataKey="name" stroke="#555" tick={{ fill: '#888', fontSize: 10 }} />
                <YAxis stroke="#555" tick={{ fill: '#888', fontSize: 10 }} />
                <Tooltip contentStyle={{ backgroundColor: '#000', border: '1px solid #333' }} itemStyle={{ color: '#35ea52' }} />
                <Line type="monotone" dataKey="trend" stroke="#35ea52" strokeWidth={2} dot={{ fill: '#35ea52', r: 4 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        );
      case "qa_gate":
        return (
          <div className="h-[250px] w-full mt-4 flex justify-center items-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={evidenceData}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={80}
                  fill="#8884d8"
                  paddingAngle={5}
                  dataKey="value"
                >
                  {evidenceData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ backgroundColor: '#000', border: '1px solid #333' }} itemStyle={{ color: '#35ea52' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        );
      default:
        return (
          <div className="h-[250px] w-full mt-4 flex items-center justify-center border border-dashed border-foreground/20">
            <p className="text-xs font-mono text-foreground/40 tracking-widest">ĐANG CHỜ DỮ LIỆU PHÂN TÍCH...</p>
          </div>
        );
    }
  };

  const getChartTitle = () => {
    switch (currentStage) {
      case "product_input": return "PHÂN TÍCH THUỘC TÍNH SẢN PHẨM";
      case "research": return "PHÂN BỐ ĐỘ TUỔI KHÁCH HÀNG";
      case "content_generation": return "XU HƯỚNG THỊ TRƯỜNG TỔNG QUAN";
      case "qa_gate": return "PHÂN BỐ NGUỒN DỮ LIỆU";
      default: return "BIỂU ĐỒ PHÂN TÍCH";
    }
  };

  return (
    <div className="border border-foreground/10 bg-background/50 h-full p-5 space-y-6 relative overflow-y-auto">
      <div className="absolute top-0 left-0 w-2 h-2 border-t border-l border-foreground/20" />
      <div className="absolute top-0 right-0 w-2 h-2 border-t border-r border-foreground/20" />

      {/* Header */}
      <div className="flex items-center gap-2">
        <div className="w-1.5 h-1.5 rounded-full bg-[#35ea52]" />
        <span className="text-xs font-mono text-foreground/50 tracking-widest uppercase">
          BẢNG.NGỮ CẢNH
        </span>
      </div>

      {/* Dynamic Chart Section */}
      <div className="space-y-3">
        <div className="flex items-center gap-2 text-[11px] font-mono text-foreground/30 border-b border-foreground/10 pb-1">
          <Activity className="h-3 w-3" />
          <span>{getChartTitle()}</span>
        </div>
        
        {renderChart()}
      </div>

      <div className="absolute bottom-0 left-0 w-2 h-2 border-b border-l border-foreground/20" />
      <div className="absolute bottom-0 right-0 w-2 h-2 border-b border-r border-foreground/20" />
    </div>
  );
};
