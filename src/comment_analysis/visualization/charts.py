"""可视化模块：将多维分析结果渲染为交互式 HTML 仪表盘。"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


_TEMPLATE = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>舆情监测编辑室 · 评论分析报告</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=Noto+Serif+SC:wght@500;700&family=Source+Sans+3:wght@400;500;600&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/echarts-wordcloud@2.1.0/dist/echarts-wordcloud.min.js"></script>
<style>
  :root {
    --bg: #0f1419;
    --card: #1a2332;
    --card-hover: #212d40;
    --border: rgba(255,255,255,0.06);
    --text: #e8ecf1;
    --muted: #8b95a8;
    --positive: #3d9970;
    --negative: #c0392b;
    --neutral: #7f8c8d;
    --accent: #e8a838;
    --serif: "Noto Serif SC", "Songti SC", serif;
    --sans: "Source Sans 3", "PingFang SC", sans-serif;
    --mono: "IBM Plex Mono", "Consolas", monospace;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: var(--sans);
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
    line-height: 1.5;
  }
  body::before {
    content: "";
    position: fixed;
    inset: 0;
    background:
      radial-gradient(ellipse 80% 50% at 20% -10%, rgba(61,153,112,0.08) 0%, transparent 60%),
      radial-gradient(ellipse 60% 40% at 90% 10%, rgba(232,168,56,0.06) 0%, transparent 50%),
      linear-gradient(180deg, #0f1419 0%, #121820 100%);
    pointer-events: none;
    z-index: 0;
  }
  body::after {
    content: "";
    position: fixed;
    inset: 0;
    opacity: 0.035;
    background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
    pointer-events: none;
    z-index: 0;
  }
  .page { position: relative; z-index: 1; }

  /* Hero */
  .hero {
    padding: 40px 32px 32px;
    border-bottom: 1px solid var(--border);
  }
  .hero-inner { max-width: 1400px; margin: 0 auto; }
  .hero-eyebrow {
    font-family: var(--mono);
    font-size: 11px;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--accent);
    margin-bottom: 10px;
  }
  .hero h1 {
    font-family: var(--serif);
    font-size: clamp(28px, 4vw, 40px);
    font-weight: 700;
    letter-spacing: 0.02em;
    margin-bottom: 12px;
  }
  .hero-meta {
    font-size: 14px;
    color: var(--muted);
    margin-bottom: 28px;
  }
  .hero-stat {
    display: inline-flex;
    flex-direction: column;
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px 32px;
    transition: transform 0.25s ease, box-shadow 0.25s ease;
  }
  .hero-stat:hover {
    transform: translateY(-3px);
    box-shadow: 0 12px 32px rgba(0,0,0,0.35);
  }
  .hero-stat .value {
    font-family: var(--mono);
    font-size: clamp(36px, 5vw, 52px);
    font-weight: 600;
    color: var(--accent);
    line-height: 1.1;
  }
  .hero-stat .label {
    font-size: 13px;
    color: var(--muted);
    margin-top: 6px;
    letter-spacing: 0.04em;
  }

  .container { max-width: 1400px; margin: 0 auto; padding: 24px 32px 48px; }

  /* Filters */
  .filters {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 16px 20px;
    margin-bottom: 24px;
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    align-items: center;
  }
  .filters label { font-size: 12px; color: var(--muted); font-weight: 500; letter-spacing: 0.03em; }
  .filters input, .filters select {
    padding: 7px 12px;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 6px;
    font-family: var(--sans);
    font-size: 13px;
    color: var(--text);
    outline: none;
  }
  .filters input:focus, .filters select:focus { border-color: var(--accent); }
  .btn {
    font-family: var(--sans);
    background: var(--accent);
    color: #0f1419;
    border: none;
    padding: 8px 18px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 13px;
    font-weight: 600;
    transition: opacity 0.2s;
  }
  .btn:hover { opacity: 0.88; }
  .btn-ghost {
    background: transparent;
    color: var(--muted);
    border: 1px solid var(--border);
  }
  .btn-ghost:hover { color: var(--text); border-color: var(--muted); opacity: 1; }

  /* Section */
  .section { margin-bottom: 28px; }
  .section-head {
    display: flex;
    align-items: baseline;
    gap: 12px;
    margin-bottom: 16px;
  }
  .section-head h2 {
    font-family: var(--serif);
    font-size: 20px;
    font-weight: 700;
  }
  .section-head .hint { font-size: 13px; color: var(--muted); }

  /* Insight strip */
  .insight-strip {
    display: flex;
    gap: 14px;
    overflow-x: auto;
    padding-bottom: 6px;
    scrollbar-width: thin;
    scrollbar-color: var(--border) transparent;
  }
  .insight-card {
    flex: 0 0 auto;
    min-width: 220px;
    max-width: 300px;
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 16px 18px;
    transition: transform 0.22s ease, border-color 0.22s ease;
  }
  .insight-card:hover {
    transform: translateY(-2px);
    border-color: rgba(232,168,56,0.25);
  }
  .insight-card .ic-title {
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--muted);
    margin-bottom: 6px;
  }
  .insight-card .ic-text {
    font-family: var(--serif);
    font-size: 16px;
    font-weight: 500;
    line-height: 1.4;
  }
  .insight-card.type-negative .ic-text { color: var(--negative); }
  .insight-card.type-positive .ic-text { color: var(--positive); }
  .insight-card.type-accent .ic-text { color: var(--accent); }

  /* Stats grid */
  .stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
    gap: 14px;
    margin-bottom: 28px;
  }
  .stat-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 16px;
    transition: transform 0.22s ease, box-shadow 0.22s ease;
  }
  .stat-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(0,0,0,0.3);
  }
  .stat-card .value {
    font-family: var(--mono);
    font-size: 26px;
    font-weight: 600;
    color: var(--text);
  }
  .stat-card .label { font-size: 12px; color: var(--muted); margin-top: 4px; }

  /* Charts */
  .charts-row {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 14px;
    margin-bottom: 14px;
  }
  @media (max-width: 960px) { .charts-row { grid-template-columns: 1fr; } }
  .chart-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 16px;
    transition: transform 0.22s ease, box-shadow 0.22s ease;
  }
  .chart-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(0,0,0,0.28);
  }
  .chart-card .title {
    font-family: var(--serif);
    font-size: 14px;
    font-weight: 600;
    margin-bottom: 10px;
    color: var(--text);
  }
  .chart { width: 100%; height: 280px; }
  .chart-tall { height: 340px; }
  .chart-wordcloud { height: 380px; }
  .full-width { grid-column: 1 / -1; }

  /* Table */
  .table-wrap {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 16px;
    overflow-x: auto;
  }
  .table-wrap .title {
    font-family: var(--serif);
    font-size: 15px;
    font-weight: 600;
    margin-bottom: 12px;
  }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  th, td { padding: 10px 12px; text-align: left; border-bottom: 1px solid var(--border); }
  th {
    background: rgba(0,0,0,0.2);
    font-weight: 600;
    color: var(--muted);
    font-size: 11px;
    letter-spacing: 0.06em;
    text-transform: uppercase;
  }
  tr:hover td { background: rgba(255,255,255,0.02); }
  .tag {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.03em;
  }
  .tag-positive { background: rgba(61,153,112,0.18); color: var(--positive); }
  .tag-negative { background: rgba(192,57,43,0.18); color: var(--negative); }
  .tag-neutral { background: rgba(127,140,141,0.18); color: var(--neutral); }
  .keyword { color: var(--accent); font-weight: 500; }
  .muted { color: var(--muted); font-size: 12px; }
  .empty { text-align: center; padding: 40px; color: var(--muted); }
  .table-note { font-size: 12px; color: var(--muted); margin-top: 10px; }
</style>
</head>
<body>
<div class="page">
  <header class="hero">
    <div class="hero-inner">
      <div class="hero-eyebrow">Sentiment Monitor · Edit Room</div>
      <h1>舆情监测编辑室</h1>
      <div class="hero-meta">生成时间：{{GENERATED_AT}} &nbsp;·&nbsp; 数据范围：{{DATE_START}} 至 {{DATE_END}}</div>
      <div class="hero-stat">
        <div class="value" id="hero-total">0</div>
        <div class="label">总评论数</div>
      </div>
    </div>
  </header>

  <div class="container">
    <div class="filters">
      <label>平台</label>
      <select id="filter-platform"><option value="">全部</option></select>
      <label>起始日期</label>
      <input type="date" id="filter-start">
      <label>结束日期</label>
      <input type="date" id="filter-end">
      <label>关键词</label>
      <input type="text" id="filter-keyword" placeholder="输入关键词">
      <label>情感</label>
      <select id="filter-sentiment">
        <option value="">全部</option>
        <option value="积极">积极</option>
        <option value="中性">中性</option>
        <option value="消极">消极</option>
      </select>
      <button class="btn" onclick="applyFilters()">筛选</button>
      <button class="btn btn-ghost" onclick="resetFilters()">重置</button>
    </div>

    <section class="section">
      <div class="section-head"><h2>洞察速览</h2><span class="hint">Insight Strip</span></div>
      <div class="insight-strip" id="insight-strip"></div>
    </section>

    <div class="stats-grid">
      <div class="stat-card"><div class="value" id="stat-platforms">0</div><div class="label">平台数</div></div>
      <div class="stat-card"><div class="value" id="stat-keywords">0</div><div class="label">关键词种类</div></div>
      <div class="stat-card"><div class="value" id="stat-avg-likes">0</div><div class="label">平均点赞</div></div>
      <div class="stat-card"><div class="value" id="stat-avg-replies">0</div><div class="label">平均回复</div></div>
      <div class="stat-card"><div class="value" id="stat-languages">0</div><div class="label">语言种类</div></div>
      <div class="stat-card"><div class="value" id="stat-negative-pct">0</div><div class="label">消极占比</div></div>
    </div>

    <section class="section">
      <div class="section-head"><h2>概览</h2><span class="hint">Overview</span></div>
      <div class="charts-row">
        <div class="chart-card"><div class="title">情感分布</div><div id="chart-sentiment" class="chart"></div></div>
        <div class="chart-card"><div class="title">平台分布</div><div id="chart-platform" class="chart"></div></div>
        <div class="chart-card"><div class="title">语言分布</div><div id="chart-language" class="chart"></div></div>
      </div>
    </section>

    <section class="section">
      <div class="section-head"><h2>焦点词云</h2><span class="hint">Focus</span></div>
      <div class="chart-card full-width">
        <div id="chart-wordcloud" class="chart chart-wordcloud"></div>
      </div>
    </section>

    <section class="section">
      <div class="section-head"><h2>热词情感交叉</h2><span class="hint">Keyword × Sentiment</span></div>
      <div class="chart-card full-width">
        <div id="chart-keyword-sentiment" class="chart chart-tall"></div>
      </div>
    </section>

    <section class="section">
      <div class="section-head"><h2>情感分数分布</h2><span class="hint">Score Histogram</span></div>
      <div class="chart-card full-width">
        <div id="chart-sentiment-score" class="chart chart-tall"></div>
      </div>
    </section>

    <section class="section">
      <div class="section-head"><h2>趋势与交叉</h2><span class="hint">Trends</span></div>
      <div class="chart-card full-width" style="margin-bottom:14px">
        <div class="title">时间趋势</div>
        <div id="chart-trend" class="chart chart-tall"></div>
      </div>
      <div class="chart-card full-width" style="margin-bottom:14px">
        <div class="title">平台 × 情感 交叉统计</div>
        <div id="chart-platform-sentiment" class="chart chart-tall"></div>
      </div>
      <div class="chart-card full-width">
        <div class="title">每日情感趋势</div>
        <div id="chart-daily-sentiment" class="chart chart-tall"></div>
      </div>
    </section>

    <div class="table-wrap">
      <div class="title">评论明细</div>
      <table>
        <thead>
          <tr><th>平台</th><th>情感</th><th>关键词</th><th>内容</th><th>点赞</th><th>回复</th><th>时间</th></tr>
        </thead>
        <tbody id="records-body"></tbody>
      </table>
      <div id="records-empty" class="empty" style="display:none;">没有符合条件的评论</div>
      <div class="table-note">最多展示 200 条记录</div>
    </div>
  </div>
</div>

<script>
const RAW_DATA = {{JSON_DATA}};

const COLORS = {
  positive: '#3d9970',
  negative: '#c0392b',
  neutral: '#7f8c8d',
  accent: '#e8a838',
  text: '#c8d0dc',
  muted: '#8b95a8',
  border: 'rgba(255,255,255,0.08)',
  card: '#1a2332',
};
const SENTIMENTS = ['积极', '中性', '消极'];
const LANG_MAP = { zh: '中文', en: '英文', mixed: '混合', unknown: '未知' };
const CHART_IDS = [
  'chart-sentiment', 'chart-platform', 'chart-language', 'chart-wordcloud',
  'chart-keyword-sentiment', 'chart-sentiment-score',
  'chart-trend', 'chart-platform-sentiment', 'chart-daily-sentiment',
];

let currentRecords = [];
let isFiltered = false;

(function registerDarkTheme() {
  echarts.registerTheme('darkRoom', {
    color: [COLORS.positive, COLORS.negative, COLORS.neutral, COLORS.accent, '#5a9a8f', '#a0522d'],
    backgroundColor: 'transparent',
    textStyle: { color: COLORS.text, fontFamily: '"Source Sans 3", sans-serif' },
    title: { textStyle: { color: COLORS.text } },
    legend: { textStyle: { color: COLORS.muted } },
    tooltip: {
      backgroundColor: 'rgba(26,35,50,0.95)',
      borderColor: COLORS.border,
      textStyle: { color: COLORS.text, fontSize: 13 },
    },
    categoryAxis: {
      axisLine: { lineStyle: { color: COLORS.border } },
      axisTick: { lineStyle: { color: COLORS.border } },
      axisLabel: { color: COLORS.muted },
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.04)' } },
    },
    valueAxis: {
      axisLine: { lineStyle: { color: COLORS.border } },
      axisTick: { lineStyle: { color: COLORS.border } },
      axisLabel: { color: COLORS.muted },
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } },
    },
  });
})();

function getRecords() { return RAW_DATA.records || []; }

function getSentimentColor(label) {
  if (label === '积极') return COLORS.positive;
  if (label === '消极') return COLORS.negative;
  return COLORS.neutral;
}

function getChart(el) {
  let chart = echarts.getInstanceByDom(el);
  if (chart) return chart;
  return echarts.init(el, 'darkRoom');
}

function setChartOption(el, option) {
  getChart(el).setOption(option, true);
}

function animateCount(el, target, opts = {}) {
  const duration = opts.duration || 600;
  const decimals = opts.decimals != null ? opts.decimals : 0;
  const suffix = opts.suffix || '';
  const start = parseFloat(el.dataset.current) || 0;
  const end = typeof target === 'number' ? target : parseFloat(target);
  if (isNaN(end)) { el.textContent = target; return; }
  const t0 = performance.now();
  function tick(now) {
    const p = Math.min((now - t0) / duration, 1);
    const eased = 1 - Math.pow(1 - p, 3);
    const val = start + (end - start) * eased;
    el.textContent = (decimals ? val.toFixed(decimals) : Math.round(val)) + suffix;
    if (p < 1) requestAnimationFrame(tick);
    else el.dataset.current = String(end);
  }
  requestAnimationFrame(tick);
}

function initFilters() {
  const platforms = [...new Set(getRecords().map(r => r.platform).filter(Boolean))];
  const sel = document.getElementById('filter-platform');
  platforms.forEach(p => {
    const o = document.createElement('option');
    o.value = p; o.textContent = p;
    sel.appendChild(o);
  });
  const dates = getRecords().map(r => r.date_label).filter(Boolean).sort();
  if (dates.length) {
    document.getElementById('filter-start').value = dates[0];
    document.getElementById('filter-end').value = dates[dates.length - 1];
  }
}

function applyFilters() {
  const platform = document.getElementById('filter-platform').value;
  const start = document.getElementById('filter-start').value;
  const end = document.getElementById('filter-end').value;
  const keyword = document.getElementById('filter-keyword').value.trim().toLowerCase();
  const sentiment = document.getElementById('filter-sentiment').value;

  currentRecords = getRecords().filter(r => {
    if (platform && r.platform !== platform) return false;
    if (start && r.date_label && r.date_label < start) return false;
    if (end && r.date_label && r.date_label > end) return false;
    if (sentiment && (r.sentiment_label || '中性') !== sentiment) return false;
    if (keyword) {
      const text = (r.content + ' ' + (r.title || '')).toLowerCase();
      const kwMatch = (r.keywords || []).some(k => k.toLowerCase().includes(keyword));
      if (!text.includes(keyword) && !kwMatch) return false;
    }
    return true;
  });
  isFiltered = true;
  updateDashboard();
}

function resetFilters() {
  document.getElementById('filter-platform').value = '';
  document.getElementById('filter-sentiment').value = '';
  document.getElementById('filter-keyword').value = '';
  const dates = getRecords().map(r => r.date_label).filter(Boolean).sort();
  if (dates.length) {
    document.getElementById('filter-start').value = dates[0];
    document.getElementById('filter-end').value = dates[dates.length - 1];
  }
  currentRecords = getRecords();
  isFiltered = false;
  updateDashboard();
}

function computeClientInsights(records) {
  const total = records.length;
  const neg = records.filter(r => (r.sentiment_label || '中性') === '消极').length;
  const negPct = total ? ((neg / total) * 100).toFixed(1) : '0.0';
  const kw = {};
  records.forEach(r => (r.keywords || []).forEach(k => { kw[k] = (kw[k] || 0) + 1; }));
  const topKw = Object.entries(kw).sort((a, b) => b[1] - a[1])[0];
  const pos = records.filter(r => (r.sentiment_label || '中性') === '积极').length;
  const insights = [
    { title: '评论总量', text: total + ' 条', type: 'accent' },
    { title: '消极占比', text: negPct + '%', type: 'negative' },
    { title: '积极评论', text: pos + ' 条', type: 'positive' },
  ];
  if (topKw) insights.push({ title: '热词榜首', text: topKw[0] + ' (' + topKw[1] + ')', type: 'accent' });
  return insights;
}

function normalizeInsight(item) {
  if (typeof item === 'string') return { title: '洞察', text: item, type: '' };
  return {
    title: item.title || item.label || '洞察',
    text: item.text || item.value || item.content || '',
    type: item.type || item.sentiment || '',
  };
}

function renderInsights(insights) {
  const strip = document.getElementById('insight-strip');
  strip.innerHTML = '';
  if (!insights.length) {
    strip.innerHTML = '<div class="insight-card"><div class="ic-text muted">暂无洞察数据</div></div>';
    return;
  }
  insights.forEach(item => {
    const ins = normalizeInsight(item);
    const card = document.createElement('div');
    card.className = 'insight-card' + (ins.type ? ' type-' + ins.type : '');
    card.innerHTML = '<div class="ic-title">' + ins.title + '</div><div class="ic-text">' + ins.text + '</div>';
    strip.appendChild(card);
  });
}

function updateInsights() {
  if (isFiltered || !(RAW_DATA.insights && RAW_DATA.insights.length)) {
    renderInsights(computeClientInsights(currentRecords));
  } else {
    renderInsights(RAW_DATA.insights);
  }
}

function updateStats() {
  animateCount(document.getElementById('hero-total'), currentRecords.length);
  const platforms = new Set(currentRecords.map(r => r.platform));
  animateCount(document.getElementById('stat-platforms'), platforms.size);
  const allKeywords = new Set();
  currentRecords.forEach(r => (r.keywords || []).forEach(k => allKeywords.add(k)));
  animateCount(document.getElementById('stat-keywords'), allKeywords.size);
  const likes = currentRecords.map(r => r.like_count).filter(v => typeof v === 'number');
  const replies = currentRecords.map(r => r.reply_count).filter(v => typeof v === 'number');
  const avgLikes = likes.length ? likes.reduce((a, b) => a + b, 0) / likes.length : null;
  const avgReplies = replies.length ? replies.reduce((a, b) => a + b, 0) / replies.length : null;
  animateCount(document.getElementById('stat-avg-likes'), avgLikes != null ? avgLikes : '-', { decimals: avgLikes != null ? 1 : 0 });
  animateCount(document.getElementById('stat-avg-replies'), avgReplies != null ? avgReplies : '-', { decimals: avgReplies != null ? 1 : 0 });
  const langSet = new Set(currentRecords.map(r => r.detected_language || 'unknown'));
  animateCount(document.getElementById('stat-languages'), langSet.size);
  const neg = currentRecords.filter(r => (r.sentiment_label || '中性') === '消极').length;
  const negPct = currentRecords.length ? (neg / currentRecords.length * 100) : 0;
  animateCount(document.getElementById('stat-negative-pct'), negPct, { decimals: 1, suffix: '%' });
}

function darkGrid() {
  return { left: '3%', right: '4%', bottom: '3%', containLabel: true };
}

function makePieOption(data) {
  return {
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: { bottom: 0, textStyle: { color: COLORS.muted } },
    series: [{
      type: 'pie',
      radius: ['42%', '68%'],
      avoidLabelOverlap: true,
      itemStyle: { borderRadius: 6, borderColor: COLORS.card, borderWidth: 2 },
      label: { color: COLORS.text, formatter: '{b}\\n{d}%' },
      data: data.map(d => ({
        value: d.count,
        name: d.label,
        itemStyle: { color: getSentimentColor(d.label) },
      })),
    }],
  };
}

function makePlatformPieOption(data) {
  const palette = [COLORS.accent, COLORS.positive, '#5a9a8f', '#a0522d', COLORS.neutral, '#6b7b8d'];
  return {
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: { bottom: 0, textStyle: { color: COLORS.muted } },
    series: [{
      type: 'pie',
      radius: ['42%', '68%'],
      itemStyle: { borderRadius: 6, borderColor: COLORS.card, borderWidth: 2 },
      label: { color: COLORS.text, formatter: '{b}\\n{d}%' },
      data: data.map((d, i) => ({ value: d.count, name: d.label, itemStyle: { color: palette[i % palette.length] } })),
    }],
  };
}

function makeBarOption(data, color) {
  return {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: darkGrid(),
    xAxis: {
      type: 'category',
      data: data.map(d => d.label),
      axisLabel: { interval: 0, rotate: data.length > 10 ? 30 : 0, color: COLORS.muted },
    },
    yAxis: { type: 'value' },
    series: [{
      data: data.map(d => d.count),
      type: 'bar',
      itemStyle: { color: color || COLORS.accent, borderRadius: [4, 4, 0, 0] },
    }],
  };
}

function aggregateRecords(records) {
  const sentimentData = {}, platformData = {}, languageData = {};
  const dailyData = {}, keywordData = {};
  const platformSentiment = {}, dailySentiment = {};
  const keywordSentiment = {};

  records.forEach(r => {
    const s = r.sentiment_label || '中性';
    sentimentData[s] = (sentimentData[s] || 0) + 1;
    platformData[r.platform] = (platformData[r.platform] || 0) + 1;
    const lang = r.detected_language || 'unknown';
    languageData[lang] = (languageData[lang] || 0) + 1;
    if (r.date_label) dailyData[r.date_label] = (dailyData[r.date_label] || 0) + 1;
    (r.keywords || []).forEach(k => {
      keywordData[k] = (keywordData[k] || 0) + 1;
      if (!keywordSentiment[k]) keywordSentiment[k] = {};
      keywordSentiment[k][s] = (keywordSentiment[k][s] || 0) + 1;
    });
    if (!platformSentiment[r.platform]) platformSentiment[r.platform] = {};
    platformSentiment[r.platform][s] = (platformSentiment[r.platform][s] || 0) + 1;
    if (r.date_label) {
      if (!dailySentiment[r.date_label]) dailySentiment[r.date_label] = {};
      dailySentiment[r.date_label][s] = (dailySentiment[r.date_label][s] || 0) + 1;
    }
  });

  return {
    sentimentList: Object.entries(sentimentData).map(([label, count]) => ({ label, count })).sort((a, b) => b.count - a.count),
    platformList: Object.entries(platformData).map(([label, count]) => ({ label, count })).sort((a, b) => b.count - a.count),
    languageList: Object.entries(languageData).map(([label, count]) => ({ label, count })).sort((a, b) => b.count - a.count),
    dailyList: Object.entries(dailyData).map(([label, count]) => ({ label, count })).sort((a, b) => a.label.localeCompare(b.label)),
    keywordList: Object.entries(keywordData).map(([label, count]) => ({ label, count })).sort((a, b) => b.count - a.count),
    platformSentiment,
    dailySentiment,
    keywordSentiment,
  };
}

function buildWordCloudData(records) {
  if (!isFiltered && RAW_DATA.word_cloud && RAW_DATA.word_cloud.length) {
    return RAW_DATA.word_cloud.map(item => ({
      name: item.word || item.name || item.label,
      value: item.weight || item.value || item.count || 1,
    }));
  }
  const agg = aggregateRecords(records);
  return agg.keywordList.slice(0, 80).map(d => ({ name: d.label, value: d.count }));
}

function buildKeywordSentimentBreakdown(records) {
  if (!isFiltered && RAW_DATA.keyword_sentiment_breakdown && RAW_DATA.keyword_sentiment_breakdown.length) {
    return RAW_DATA.keyword_sentiment_breakdown.slice(0, 20);
  }
  const agg = aggregateRecords(records);
  return agg.keywordList.slice(0, 20).map(d => ({
    keyword: d.label,
    total: d.count,
    sentiments: SENTIMENTS.map(s => ({
      label: s,
      count: (agg.keywordSentiment[d.label] && agg.keywordSentiment[d.label][s]) || 0,
    })),
  }));
}

function buildSentimentScoreHistogram(records) {
  if (!isFiltered && RAW_DATA.sentiment_score_summary && RAW_DATA.sentiment_score_summary.histogram) {
    const hist = RAW_DATA.sentiment_score_summary.histogram;
    if (hist.length) return hist;
  }
  const scores = records.map(r => r.sentiment_score).filter(v => typeof v === 'number');
  if (!scores.length) return [];
  const bins = 10;
  const min = -1, max = 1;
  const step = (max - min) / bins;
  const counts = Array(bins).fill(0);
  scores.forEach(s => {
    let idx = Math.floor((s - min) / step);
    if (idx >= bins) idx = bins - 1;
    if (idx < 0) idx = 0;
    counts[idx]++;
  });
  return counts.map((count, i) => ({
    bin: (min + i * step).toFixed(1) + '~' + (min + (i + 1) * step).toFixed(1),
    count,
  }));
}

function updateCharts() {
  const agg = aggregateRecords(currentRecords);

  setChartOption(document.getElementById('chart-sentiment'), makePieOption(agg.sentimentList));
  setChartOption(document.getElementById('chart-platform'), makePlatformPieOption(agg.platformList));

  const langData = agg.languageList.map(d => ({
    label: LANG_MAP[d.label] || d.label,
    count: d.count,
  }));
  setChartOption(document.getElementById('chart-language'), makePlatformPieOption(langData));

  const wcData = buildWordCloudData(currentRecords);
  setChartOption(document.getElementById('chart-wordcloud'), {
    tooltip: { show: true },
    series: [{
      type: 'wordCloud',
      shape: 'circle',
      left: 'center',
      top: 'center',
      width: '95%',
      height: '95%',
      sizeRange: [14, 56],
      rotationRange: [-30, 30],
      gridSize: 8,
      drawOutOfBound: false,
      textStyle: {
        fontFamily: '"Noto Serif SC", serif',
        color: function() {
          const palette = [COLORS.accent, COLORS.positive, COLORS.negative, COLORS.neutral, '#5a9a8f'];
          return palette[Math.floor(Math.random() * palette.length)];
        },
      },
      emphasis: { textStyle: { shadowBlur: 8, shadowColor: 'rgba(232,168,56,0.4)' } },
      data: wcData,
    }],
  });

  const kwBreakdown = buildKeywordSentimentBreakdown(currentRecords);
  const kwLabels = kwBreakdown.map(d => d.keyword);
  const kwSeries = SENTIMENTS.map(s => ({
    name: s,
    type: 'bar',
    stack: 'total',
    data: kwBreakdown.map(d => {
      const found = (d.sentiments || []).find(x => x.label === s);
      return found ? found.count : 0;
    }),
    itemStyle: { color: getSentimentColor(s) },
  }));
  setChartOption(document.getElementById('chart-keyword-sentiment'), {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    legend: { data: SENTIMENTS, textStyle: { color: COLORS.muted } },
    grid: darkGrid(),
    xAxis: { type: 'category', data: kwLabels, axisLabel: { rotate: kwLabels.length > 8 ? 30 : 0, color: COLORS.muted } },
    yAxis: { type: 'value' },
    series: kwSeries,
  });

  const hist = buildSentimentScoreHistogram(currentRecords);
  if (hist.length) {
    setChartOption(document.getElementById('chart-sentiment-score'), {
      tooltip: { trigger: 'axis' },
      grid: darkGrid(),
      xAxis: { type: 'category', data: hist.map(h => h.bin || h.label), axisLabel: { color: COLORS.muted } },
      yAxis: { type: 'value', name: '评论数', nameTextStyle: { color: COLORS.muted } },
      series: [{
        type: 'bar',
        data: hist.map(h => h.count),
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: COLORS.accent },
            { offset: 1, color: 'rgba(232,168,56,0.35)' },
          ]),
          borderRadius: [4, 4, 0, 0],
        },
      }],
    });
  } else {
    setChartOption(document.getElementById('chart-sentiment-score'), {
      title: { text: '暂无情感分数数据', left: 'center', top: 'center', textStyle: { color: COLORS.muted, fontSize: 14 } },
      series: [],
    });
  }

  setChartOption(document.getElementById('chart-trend'), makeBarOption(agg.dailyList, COLORS.accent));

  const psPlatforms = Object.keys(agg.platformSentiment).sort();
  const psSeries = SENTIMENTS.map(s => ({
    name: s,
    type: 'bar',
    stack: 'total',
    data: psPlatforms.map(p => (agg.platformSentiment[p][s] || 0)),
    itemStyle: { color: getSentimentColor(s) },
  }));
  setChartOption(document.getElementById('chart-platform-sentiment'), {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    legend: { data: SENTIMENTS, textStyle: { color: COLORS.muted } },
    grid: darkGrid(),
    xAxis: { type: 'category', data: psPlatforms, axisLabel: { color: COLORS.muted } },
    yAxis: { type: 'value' },
    series: psSeries,
  });

  const dsDates = Object.keys(agg.dailySentiment).sort();
  const dsSeries = SENTIMENTS.map(s => ({
    name: s,
    type: 'line',
    smooth: true,
    data: dsDates.map(d => (agg.dailySentiment[d][s] || 0)),
    itemStyle: { color: getSentimentColor(s) },
    lineStyle: { width: 2 },
    areaStyle: { opacity: 0.08 },
  }));
  setChartOption(document.getElementById('chart-daily-sentiment'), {
    tooltip: { trigger: 'axis' },
    legend: { data: SENTIMENTS, textStyle: { color: COLORS.muted } },
    grid: darkGrid(),
    xAxis: { type: 'category', data: dsDates, axisLabel: { rotate: dsDates.length > 10 ? 30 : 0, color: COLORS.muted } },
    yAxis: { type: 'value' },
    series: dsSeries,
  });
}

function updateTable() {
  const tbody = document.getElementById('records-body');
  const empty = document.getElementById('records-empty');
  tbody.innerHTML = '';
  if (!currentRecords.length) { empty.style.display = 'block'; return; }
  empty.style.display = 'none';
  const fragment = document.createDocumentFragment();
  currentRecords.slice(0, 200).forEach(r => {
    const tr = document.createElement('tr');
    const sentiment = r.sentiment_label || '中性';
    let tagClass = 'tag-neutral';
    if (sentiment === '积极') tagClass = 'tag-positive';
    if (sentiment === '消极') tagClass = 'tag-negative';
    const kw = (r.keywords || []).map(k => '<span class="keyword">' + k + '</span>').join(' ');
    const content = (r.content || '');
    tr.innerHTML =
      '<td>' + (r.platform || '-') + '</td>' +
      '<td><span class="tag ' + tagClass + '">' + sentiment + '</span></td>' +
      '<td>' + (kw || '-') + '</td>' +
      '<td>' + content.substring(0, 120) + (content.length > 120 ? '…' : '') + '</td>' +
      '<td>' + (r.like_count != null ? r.like_count : '-') + '</td>' +
      '<td>' + (r.reply_count != null ? r.reply_count : '-') + '</td>' +
      '<td class="muted">' + (r.date_label || '-') + '</td>';
    fragment.appendChild(tr);
  });
  tbody.appendChild(fragment);
}

function updateDashboard() {
  updateStats();
  updateInsights();
  updateCharts();
  updateTable();
}

currentRecords = getRecords();
initFilters();
updateDashboard();

window.addEventListener('resize', () => {
  CHART_IDS.forEach(id => {
    const el = document.getElementById(id);
    if (el) echarts.getInstanceByDom(el)?.resize();
  });
});
</script>
</body>
</html>
'''


def render_analysis_report(report: dict[str, Any]) -> str:
    """将分析结果渲染为交互式 HTML 字符串。"""
    date_range = report.get("date_range") or {}
    return (
        _TEMPLATE
        .replace("{{GENERATED_AT}}", str(report.get("generated_at", "未知")))
        .replace("{{DATE_START}}", str(date_range.get("start") or "未知"))
        .replace("{{DATE_END}}", str(date_range.get("end") or "未知"))
        .replace("{{JSON_DATA}}", json.dumps(report, ensure_ascii=False))
    )


def write_analysis_report(
    report: dict[str, Any],
    output_dir: Path,
    stem: str,
) -> Path:
    """将交互式 HTML 报告写入本地磁盘。"""
    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    output_path = target_dir / f"{stem}_dashboard.html"
    output_path.write_text(render_analysis_report(report), encoding="utf-8")
    return output_path
