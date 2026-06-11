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
<title>评论分析结果报告</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
<style>
  * { box-sizing: border-box; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    margin: 0;
    padding: 0;
    background: #f5f6fa;
    color: #333;
  }
  .header {
    background: linear-gradient(90deg, #4a69bd, #6a89cc);
    color: #fff;
    padding: 24px 32px;
  }
  .header h1 { margin: 0 0 8px 0; font-size: 24px; }
  .header .meta { opacity: 0.9; font-size: 14px; }
  .container { padding: 24px 32px; max-width: 1400px; margin: 0 auto; }
  .filters {
    background: #fff;
    border-radius: 8px;
    padding: 16px 20px;
    margin-bottom: 20px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    align-items: center;
  }
  .filters label { font-size: 13px; color: #666; font-weight: 500; }
  .filters input, .filters select {
    padding: 6px 10px;
    border: 1px solid #dcdcdc;
    border-radius: 6px;
    font-size: 13px;
    outline: none;
  }
  .filters input:focus, .filters select:focus { border-color: #4a69bd; }
  .btn {
    background: #4a69bd;
    color: #fff;
    border: none;
    padding: 7px 16px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 13px;
  }
  .btn:hover { background: #3c5aa6; }
  .stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
    gap: 16px;
    margin-bottom: 20px;
  }
  .stat-card {
    background: #fff;
    border-radius: 8px;
    padding: 16px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  }
  .stat-card .value { font-size: 28px; font-weight: 700; color: #4a69bd; }
  .stat-card .label { font-size: 13px; color: #888; margin-top: 4px; }
  .charts-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(420px, 1fr));
    gap: 16px;
    margin-bottom: 20px;
  }
  .chart-card {
    background: #fff;
    border-radius: 8px;
    padding: 16px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  }
  .chart-card .title { font-size: 15px; font-weight: 600; margin-bottom: 10px; color: #444; }
  .chart { width: 100%; height: 300px; }
  .full-width { grid-column: 1 / -1; }
  .table-wrap {
    background: #fff;
    border-radius: 8px;
    padding: 16px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    overflow-x: auto;
  }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  th, td { padding: 10px 12px; text-align: left; border-bottom: 1px solid #eee; }
  th { background: #f8f9fb; font-weight: 600; color: #555; }
  tr:hover { background: #f8f9fb; }
  .tag {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 12px;
    font-weight: 500;
  }
  .tag-positive { background: #e6f7ed; color: #237a52; }
  .tag-negative { background: #fce8e8; color: #a82828; }
  .tag-neutral { background: #f0f0f0; color: #555; }
  .keyword { color: #4a69bd; font-weight: 500; }
  .muted { color: #999; font-size: 12px; }
  .empty { text-align: center; padding: 40px; color: #999; }
</style>
</head>
<body>
<div class="header">
  <h1>评论分析结果报告</h1>
  <div class="meta">生成时间：{{GENERATED_AT}} &nbsp;|&nbsp; 数据范围：{{DATE_START}} 至 {{DATE_END}}</div>
</div>
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
    <select id="filter-sentiment"><option value="">全部</option><option value="积极">积极</option><option value="中性">中性</option><option value="消极">消极</option></select>
    <button class="btn" onclick="applyFilters()">筛选</button>
    <button class="btn" style="background:#6c757d" onclick="resetFilters()">重置</button>
  </div>

  <div class="stats-grid">
    <div class="stat-card"><div class="value" id="stat-total">0</div><div class="label">总评论数</div></div>
    <div class="stat-card"><div class="value" id="stat-platforms">0</div><div class="label">平台数</div></div>
    <div class="stat-card"><div class="value" id="stat-keywords">0</div><div class="label">关键词种类</div></div>
    <div class="stat-card"><div class="value" id="stat-avg-likes">0</div><div class="label">平均点赞</div></div>
    <div class="stat-card"><div class="value" id="stat-avg-replies">0</div><div class="label">平均回复</div></div>
    <div class="stat-card"><div class="value" id="stat-languages">0</div><div class="label">语言种类</div></div>
  </div>

  <div class="charts-grid">
    <div class="chart-card"><div class="title">情感分布</div><div id="chart-sentiment" class="chart"></div></div>
    <div class="chart-card"><div class="title">平台分布</div><div id="chart-platform" class="chart"></div></div>
    <div class="chart-card"><div class="title">语言分布</div><div id="chart-language" class="chart"></div></div>
    <div class="chart-card full-width"><div class="title">时间趋势</div><div id="chart-trend" class="chart"></div></div>
    <div class="chart-card full-width"><div class="title">热词榜</div><div id="chart-keywords" class="chart"></div></div>
    <div class="chart-card full-width"><div class="title">平台 × 情感 交叉统计</div><div id="chart-platform-sentiment" class="chart"></div></div>
    <div class="chart-card full-width"><div class="title">每日情感趋势</div><div id="chart-daily-sentiment" class="chart"></div></div>
  </div>

  <div class="table-wrap">
    <div class="title" style="font-size:15px;font-weight:600;margin-bottom:10px;color:#444;">评论明细</div>
    <table>
      <thead>
        <tr><th>平台</th><th>情感</th><th>关键词</th><th>内容</th><th>点赞</th><th>回复</th><th>时间</th></tr>
      </thead>
      <tbody id="records-body"></tbody>
    </table>
    <div id="records-empty" class="empty" style="display:none;">没有符合条件的评论</div>
  </div>
</div>

<script>
const RAW_DATA = {{JSON_DATA}};

function getRecords() { return RAW_DATA.records || []; }
function getSentimentColor(label) {
  if (label === '积极') return '#52c41a';
  if (label === '消极') return '#ff4d4f';
  return '#bfbfbf';
}

let currentRecords = getRecords();

function initFilters() {
  const platforms = [...new Set(getRecords().map(r => r.platform).filter(Boolean))];
  const sel = document.getElementById('filter-platform');
  platforms.forEach(p => { const o = document.createElement('option'); o.value = p; o.textContent = p; sel.appendChild(o); });
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
  updateDashboard();
}

function updateStats() {
  document.getElementById('stat-total').textContent = currentRecords.length;
  const platforms = new Set(currentRecords.map(r => r.platform));
  document.getElementById('stat-platforms').textContent = platforms.size;
  const allKeywords = new Set();
  currentRecords.forEach(r => (r.keywords || []).forEach(k => allKeywords.add(k)));
  document.getElementById('stat-keywords').textContent = allKeywords.size;
  const likes = currentRecords.map(r => r.like_count).filter(v => typeof v === 'number');
  const replies = currentRecords.map(r => r.reply_count).filter(v => typeof v === 'number');
  document.getElementById('stat-avg-likes').textContent = likes.length ? (likes.reduce((a,b)=>a+b,0)/likes.length).toFixed(1) : '-';
  document.getElementById('stat-avg-replies').textContent = replies.length ? (replies.reduce((a,b)=>a+b,0)/replies.length).toFixed(1) : '-';
  const langDist = RAW_DATA.language_distribution || [];
  document.getElementById('stat-languages').textContent = langDist.length;
}

function makeBarOption(title, data, color) {
  return {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', data: data.map(d => d.label), axisLabel: { interval: 0, rotate: data.length > 10 ? 30 : 0 } },
    yAxis: { type: 'value' },
    series: [{ data: data.map(d => d.count), type: 'bar', itemStyle: { color: color || '#4a69bd' } }]
  };
}

function renderLanguageChart() {
  const data = RAW_DATA.language_distribution || [];
  const el = document.getElementById('chart-language');
  if (!el) return;
  const chart = echarts.init(el);
  const labelMap = { zh: '中文', en: '英文', mixed: '混合', unknown: '未知' };
  chart.setOption({
    tooltip: { trigger: 'item' },
    series: [{
      type: 'pie',
      radius: ['35%', '65%'],
      data: data.map(d => ({ name: labelMap[d.label] || d.label, value: d.count }))
    }]
  });
}

function makePieOption(title, data) {
  return {
    tooltip: { trigger: 'item' },
    legend: { bottom: 0 },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      avoidLabelOverlap: false,
      itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
      label: { show: true, formatter: '{b}: {c} ({d}%)' },
      data: data.map(d => ({ value: d.count, name: d.label }))
    }]
  };
}

function updateCharts() {
  const sentimentData = {};
  const platformData = {};
  const dailyData = {};
  const keywordData = {};
  const platformSentiment = {};
  const dailySentiment = {};

  currentRecords.forEach(r => {
    const s = r.sentiment_label || '中性';
    sentimentData[s] = (sentimentData[s] || 0) + 1;
    platformData[r.platform] = (platformData[r.platform] || 0) + 1;
    if (r.date_label) { dailyData[r.date_label] = (dailyData[r.date_label] || 0) + 1; }
    (r.keywords || []).forEach(k => { keywordData[k] = (keywordData[k] || 0) + 1; });
    if (!platformSentiment[r.platform]) platformSentiment[r.platform] = {};
    platformSentiment[r.platform][s] = (platformSentiment[r.platform][s] || 0) + 1;
    if (r.date_label) {
      if (!dailySentiment[r.date_label]) dailySentiment[r.date_label] = {};
      dailySentiment[r.date_label][s] = (dailySentiment[r.date_label][s] || 0) + 1;
    }
  });

  const sentimentList = Object.entries(sentimentData).map(([label, count]) => ({label, count})).sort((a,b)=>b.count-a.count);
  const platformList = Object.entries(platformData).map(([label, count]) => ({label, count})).sort((a,b)=>b.count-a.count);
  const dailyList = Object.entries(dailyData).map(([label, count]) => ({label, count})).sort((a,b)=>a.label.localeCompare(b.label));
  const keywordList = Object.entries(keywordData).map(([label, count]) => ({label, count})).sort((a,b)=>b.count-a.count).slice(0, 30);

  echarts.init(document.getElementById('chart-sentiment')).setOption(makePieOption('情感分布', sentimentList));
  echarts.init(document.getElementById('chart-platform')).setOption(makePieOption('平台分布', platformList));
  renderLanguageChart();
  echarts.init(document.getElementById('chart-trend')).setOption(makeBarOption('时间趋势', dailyList, '#6a89cc'));
  echarts.init(document.getElementById('chart-keywords')).setOption(makeBarOption('热词榜', keywordList, '#4a69bd'));

  const psPlatforms = Object.keys(platformSentiment).sort();
  const psSentiments = ['积极','中性','消极'];
  const psSeries = psSentiments.map(s => ({
    name: s,
    type: 'bar',
    stack: 'total',
    data: psPlatforms.map(p => platformSentiment[p][s] || 0),
    itemStyle: { color: getSentimentColor(s) }
  }));
  echarts.init(document.getElementById('chart-platform-sentiment')).setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    legend: { data: psSentiments },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', data: psPlatforms },
    yAxis: { type: 'value' },
    series: psSeries
  });

  const dsDates = Object.keys(dailySentiment).sort();
  const dsSeries = psSentiments.map(s => ({
    name: s,
    type: 'line',
    smooth: true,
    data: dsDates.map(d => dailySentiment[d][s] || 0),
    itemStyle: { color: getSentimentColor(s) }
  }));
  echarts.init(document.getElementById('chart-daily-sentiment')).setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: psSentiments },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', data: dsDates, axisLabel: { rotate: dsDates.length > 10 ? 30 : 0 } },
    yAxis: { type: 'value' },
    series: dsSeries
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
    const kw = (r.keywords || []).map(k => `<span class="keyword">${k}</span>`).join(' ');
    tr.innerHTML = `
      <td>${r.platform || '-'}</td>
      <td><span class="tag ${tagClass}">${sentiment}</span></td>
      <td>${kw || '-'}</td>
      <td>${(r.content || '').substring(0, 120)}${(r.content || '').length > 120 ? '…' : ''}</td>
      <td>${r.like_count != null ? r.like_count : '-'}</td>
      <td>${r.reply_count != null ? r.reply_count : '-'}</td>
      <td class="muted">${r.date_label || '-'}</td>
    `;
    fragment.appendChild(tr);
  });
  tbody.appendChild(fragment);
}

function updateDashboard() {
  updateStats();
  updateCharts();
  updateTable();
}

initFilters();
updateDashboard();
window.addEventListener('resize', () => {
  ['chart-sentiment','chart-platform','chart-language','chart-trend','chart-keywords','chart-platform-sentiment','chart-daily-sentiment']
    .forEach(id => { const el = document.getElementById(id); if(el) echarts.getInstanceByDom(el)?.resize(); });
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
