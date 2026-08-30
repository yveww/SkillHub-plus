(function() {
  var style = getComputedStyle(document.documentElement);
  var accent = style.getPropertyValue('--accent').trim();
  var accent2 = style.getPropertyValue('--accent2').trim();
  var ink = style.getPropertyValue('--ink').trim();
  var muted = style.getPropertyValue('--muted').trim();
  var rule = style.getPropertyValue('--rule').trim();
  var bg2 = style.getPropertyValue('--bg2').trim();

  var passColor = '#22c55e';
  var warnColor = '#f59e0b';
  var failColor = '#ef4444';

  // --- Chart 1: Module Summary ---
  var chart1 = echarts.init(document.getElementById('chart-module-summary'), null, { renderer: 'svg' });
  chart1.setOption({
    animation: false,
    tooltip: { trigger: 'item', appendToBody: true },
    legend: { bottom: 0, left: 'center', textStyle: { color: muted, fontSize: 13 } },
    series: [{
      type: 'pie',
      radius: ['45%', '70%'],
      center: ['50%', '45%'],
      avoidLabelOverlap: false,
      label: { show: true, color: ink, fontSize: 14, formatter: '{b}\n{c} 个' },
      labelLine: { show: true },
      data: [
        { value: 5, name: '通过', itemStyle: { color: passColor } },
        { value: 3, name: '部分通过', itemStyle: { color: warnColor } },
        { value: 1, name: '失败', itemStyle: { color: failColor } },
      ]
    }]
  });
  window.addEventListener('resize', function() { chart1.resize(); });

  // --- Chart 2: Risk Heatmap ---
  var riskModules = ['表格结构', '记录CRUD', 'AI分流', '版本管理', 'Fork合并', '看板视图', '反馈表单', 'IM通知', '端到端'];
  var riskTypes = ['数据一致性', 'API稳定性', '权限范围', '并发安全', '用户体验'];

  var heatmapData = [
    [0, 0, 2], [0, 1, 1], [0, 2, 0], [0, 3, 0], [0, 4, 0],
    [1, 0, 2], [1, 1, 2], [1, 2, 0], [1, 3, 1], [1, 4, 0],
    [2, 0, 1], [2, 1, 1], [2, 2, 0], [2, 3, 0], [2, 4, 2],
    [3, 0, 1], [3, 1, 1], [3, 2, 0], [3, 3, 0], [3, 4, 0],
    [4, 0, 1], [4, 1, 2], [4, 2, 0], [4, 3, 2], [4, 4, 1],
    [5, 0, 0], [5, 1, 1], [5, 2, 2], [5, 3, 0], [5, 4, 1],
    [6, 0, 0], [6, 1, 1], [6, 2, 1], [6, 3, 0], [6, 4, 2],
    [7, 0, 0], [7, 1, 1], [7, 2, 3], [7, 3, 0], [7, 4, 1],
    [8, 0, 2], [8, 1, 2], [8, 2, 1], [8, 3, 2], [8, 4, 1],
  ];

  var chart2 = echarts.init(document.getElementById('chart-risk-matrix'), null, { renderer: 'svg' });
  chart2.setOption({
    animation: false,
    tooltip: {
      appendToBody: true,
      formatter: function(p) {
        var levels = ['低', '中', '高', '严重'];
        return riskModules[p.value[1]] + ' - ' + riskTypes[p.value[0]] + '<br/>风险等级: ' + levels[p.value[2]];
      }
    },
    grid: { top: 30, right: 20, bottom: 80, left: 100 },
    xAxis: {
      type: 'category',
      data: riskTypes,
      axisLabel: { color: muted, fontSize: 12 },
      axisLine: { lineStyle: { color: rule } },
      splitArea: { show: false }
    },
    yAxis: {
      type: 'category',
      data: riskModules,
      axisLabel: { color: muted, fontSize: 12 },
      axisLine: { lineStyle: { color: rule } },
      splitArea: { show: false }
    },
    visualMap: {
      min: 0, max: 3,
      calculable: true,
      orient: 'horizontal',
      left: 'center',
      bottom: 10,
      textStyle: { color: muted, fontSize: 12 },
      inRange: { color: ['#22c55e', '#f59e0b', '#ef4444', '#991b1b'] },
      text: ['严重', '低']
    },
    series: [{
      type: 'heatmap',
      data: heatmapData.map(function(d) { return [d[0], d[1], d[2]]; }),
      label: {
        show: true,
        color: '#fff',
        fontSize: 11,
        formatter: function(p) {
          var levels = ['低', '中', '高', '严重'];
          return levels[p.value[2]];
        }
      },
      emphasis: { itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0,0,0,0.3)' } }
    }]
  });
  window.addEventListener('resize', function() { chart2.resize(); });

  // --- Chart 3: Test Case Distribution ---
  var chart3 = echarts.init(document.getElementById('chart-test-dist'), null, { renderer: 'svg' });
  chart3.setOption({
    animation: false,
    tooltip: { trigger: 'axis', appendToBody: true, axisPointer: { type: 'shadow' } },
    legend: { bottom: 0, left: 'center', textStyle: { color: muted, fontSize: 12 } },
    grid: { top: 30, right: 20, bottom: 60, left: 50 },
    xAxis: {
      type: 'value',
      axisLabel: { color: muted, fontSize: 12 },
      axisLine: { lineStyle: { color: rule } },
      splitLine: { lineStyle: { color: rule, type: 'dashed' } }
    },
    yAxis: {
      type: 'category',
      data: ['表格结构', '记录CRUD', 'AI分流', '版本管理', 'Fork合并', '看板视图', '反馈表单', 'IM通知', '端到端'],
      axisLabel: { color: muted, fontSize: 11 },
      axisLine: { lineStyle: { color: rule } }
    },
    series: [
      {
        name: '通过',
        type: 'bar',
        stack: 'total',
        data: [3, 4, 3, 2, 3, 2, 2, 2, 3],
        itemStyle: { color: passColor }
      },
      {
        name: '部分通过',
        type: 'bar',
        stack: 'total',
        data: [1, 1, 2, 1, 1, 1, 1, 0, 1],
        itemStyle: { color: warnColor }
      },
      {
        name: '失败',
        type: 'bar',
        stack: 'total',
        data: [0, 0, 0, 0, 0, 0, 1, 1, 0],
        itemStyle: { color: failColor }
      }
    ]
  });
  window.addEventListener('resize', function() { chart3.resize(); });
})();
