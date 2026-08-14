(() => {
  const nested = location.pathname.includes('/company/') || location.pathname.includes('/sources/');
  const prefix = nested ? '../' : './';
  const state = { jobs: [], stats: {}, filtered: [], selectedCities: new Set(), page: 1, pageSize: 24 };
  const $ = (id) => document.getElementById(id);
  const esc = (value) => String(value ?? '').replace(/[&<>'"]/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[char]));
  const fmtDate = (value) => value ? value.slice(0, 10) : '未公开';
  const daysFrom = (value) => value ? Math.floor((Date.now() - new Date(`${value.slice(0,10)}T00:00:00+08:00`)) / 86400000) : Infinity;

  function applyTheme() {
    const stored = localStorage.getItem('ejr-theme') || 'system';
    const dark = stored === 'dark' || (stored === 'system' && matchMedia('(prefers-color-scheme: dark)').matches);
    document.documentElement.dataset.theme = dark ? 'dark' : 'light';
    if ($('themeButton')) $('themeButton').title = `当前：${stored}（点击切换）`;
  }
  function cycleTheme() {
    const current = localStorage.getItem('ejr-theme') || 'system';
    localStorage.setItem('ejr-theme', current === 'system' ? 'light' : current === 'light' ? 'dark' : 'system');
    applyTheme();
  }
  applyTheme();
  $('themeButton')?.addEventListener('click', cycleTheme);

  function trustBadge(job) {
    if (job.official_verified) return '<span class="badge official">OFFICIAL</span>';
    if ((job.source_count || 1) > 1) return '<span class="badge">VERIFIED · MULTI-SOURCE</span>';
    if (job.source_tier === 3) return '<span class="badge warn">AGGREGATED</span>';
    return '<span class="badge warn">UNVERIFIED</span>';
  }
  function jobCard(job) {
    const cities = job.city?.length ? job.city.join(' · ') : esc(job.location_raw || '地点未公开');
    const tags = [...(job.topics || []), ...(job.skills || [])].slice(0, 6).map(tag => `<span class="tag">${esc(tag)}</span>`).join('');
    const reasons = (job.match_reasons?.length ? job.match_reasons : ['当前信息不足，建议阅读原始来源']).map(x => `<li>${esc(x)}</li>`).join('');
    const gaps = (job.skill_gaps?.length ? job.skill_gaps : ['未发现明确硬性短板；仍需核对完整 JD']).map(x => `<li>${esc(x)}</li>`).join('');
    const link = job.official_apply_url || job.source_url;
    const companyHref = `${prefix}company/?name=${encodeURIComponent(job.company)}`;
    return `<article class="job-card" data-id="${esc(job.id)}"><div><header><div><a class="company-link" href="${companyHref}">${esc(job.company)} →</a><h3>${esc(job.title)}</h3></div><div class="badge-row">${trustBadge(job)}${job.first_seen === new Date().toISOString().slice(0,10) ? '<span class="badge">NEW</span>' : ''}${job.status === 'closing_soon' ? '<span class="badge warn">CLOSING SOON</span>' : ''}</div></header><div class="job-meta">${esc(cities)} · ${esc(job.degree || '未公开')} · ${job.graduate_year?.length ? job.graduate_year.join('/') + '届' : '届次未公开'} · ${esc(job.job_type)}</div><div class="tag-row">${tags}</div><div class="analysis"><div><h4>为什么适合我</h4><ul class="reasons">${reasons}</ul></div><div><h4>我的短板</h4><ul class="gaps">${gaps}</ul></div></div><div class="dates"><span>发布 ${fmtDate(job.published_date)}</span><span>截止 ${fmtDate(job.deadline)}</span><span>最后核验 ${fmtDate(job.last_verified)}</span><span>来源 ${esc(job.source_name)}</span></div></div><aside class="score-column"><div><small>MATCH SCORE</small><div class="score">${job.match_score ?? '—'} <b>${esc(job.match_level || '')}</b></div><div class="recommendation">${esc(job.recommendation || '等待分析')}</div></div><a class="apply-button ${job.official_apply_url ? '' : 'secondary'}" href="${esc(link)}" target="_blank" rel="noopener noreferrer">${job.official_apply_url ? '官网投递' : '查看来源'} →</a></aside></article>`;
  }

  function recommendedScore(job) {
    const score = job.match_score || 0;
    const freshness = Math.max(0, 12 - daysFrom(job.first_seen));
    const official = job.official_verified ? 8 : 0;
    let deadline = 0;
    if (job.deadline) { const d = Math.ceil((new Date(`${job.deadline}T23:59:00+08:00`) - Date.now()) / 86400000); deadline = d >= 0 && d <= 14 ? 6 : 0; }
    return score + freshness + official + deadline;
  }
  function sortJobs(jobs, mode) {
    return [...jobs].sort((a,b) => {
      if (mode === 'published') return (b.published_date || '').localeCompare(a.published_date || '');
      if (mode === 'seen') return (b.first_seen || '').localeCompare(a.first_seen || '');
      if (mode === 'match') return (b.match_score || -1) - (a.match_score || -1);
      if (mode === 'deadline') return (a.deadline || '9999').localeCompare(b.deadline || '9999');
      if (mode === 'company') return a.company.localeCompare(b.company, 'zh-CN');
      return recommendedScore(b) - recommendedScore(a);
    });
  }
  function renderPriority() {
    const jobs = sortJobs(state.jobs.filter(job => ['open','closing_soon'].includes(job.status) && !job.doctoral_exclusive), 'recommended').slice(0,3);
    $('priorityJobs').innerHTML = jobs.map((job,index) => `<a class="priority-card" href="#jobs" data-priority-id="${esc(job.id)}"><span class="rank">0${index+1} · ${job.official_verified ? 'OFFICIAL' : 'DISCOVERY'}</span><h3>${esc(job.title)}</h3><span class="company">${esc(job.company)} · ${esc(job.city?.join(' / ') || '地点未公开')}</span><div class="priority-footer"><div><small>MATCH</small><strong>${job.match_score ?? '—'}<small>${esc(job.match_level || '')}</small></strong></div><span>查看岗位 →</span></div></a>`).join('') || '<div class="empty">暂无可排序的开放岗位</div>';
    document.querySelectorAll('[data-priority-id]').forEach(el => el.addEventListener('click', () => { const id = el.dataset.priorityId; setTimeout(() => document.querySelector(`[data-id="${CSS.escape(id)}"]`)?.scrollIntoView({block:'center'}), 60); }));
  }
  function populateFilters() {
    const topics = [...new Set(state.jobs.flatMap(job => job.topics || []))].sort((a,b) => a.localeCompare(b,'zh-CN'));
    $('topicFilter').insertAdjacentHTML('beforeend', topics.map(topic => `<option>${esc(topic)}</option>`).join(''));
    renderCities('');
  }
  function renderCities(query) {
    const priority = ['北京','上海','深圳','杭州','苏州'];
    const all = [...new Set(state.jobs.flatMap(job => job.city || []))];
    const cities = [...priority.filter(x => all.includes(x)), ...all.filter(x => !priority.includes(x)).sort((a,b)=>a.localeCompare(b,'zh-CN'))].filter(city => city.includes(query));
    $('cityOptions').innerHTML = cities.map(city => `<label><input type="checkbox" value="${esc(city)}" ${state.selectedCities.has(city) ? 'checked' : ''}><span>${esc(city)}</span></label>`).join('') || '<small>未找到城市</small>';
    $('cityOptions').querySelectorAll('input').forEach(input => input.addEventListener('change', () => { input.checked ? state.selectedCities.add(input.value) : state.selectedCities.delete(input.value); state.page = 1; applyFilters(); }));
  }
  function applyFilters() {
    const q = $('searchInput').value.trim().toLowerCase();
    const topic = $('topicFilter').value, degree = $('degreeFilter').value, type = $('typeFilter').value;
    const minScore = Number($('scoreFilter').value), status = $('statusFilter').value, days = Number($('timeFilter').value), includeDoctoral = $('doctoralToggle').checked;
    state.filtered = state.jobs.filter(job => {
      const haystack = [job.company,job.title,job.description,job.location_raw,...(job.city||[]),...(job.skills||[]),...(job.topics||[]),...(job.requirements||[])].join(' ').toLowerCase();
      if (q && !haystack.includes(q)) return false;
      if (topic && !(job.topics || []).includes(topic)) return false;
      if (state.selectedCities.size && !(job.city || []).some(city => state.selectedCities.has(city))) return false;
      if (degree && !(job.degree || '').includes(degree) && !(degree === '硕士' && ['本科及以上','不限','未公开'].includes(job.degree))) return false;
      if (type && job.job_type !== type) return false;
      if ((job.match_score || 0) < minScore) return false;
      if (status === 'active' && !['open','closing_soon'].includes(job.status)) return false;
      if (status !== 'active' && status !== 'all' && job.status !== status) return false;
      if (days && daysFrom(job.first_seen) >= days) return false;
      if (!includeDoctoral && job.doctoral_exclusive) return false;
      return true;
    });
    state.filtered = sortJobs(state.filtered, $('sortSelect').value);
    renderJobs();
  }
  function renderJobs() {
    const visible = state.filtered.slice(0, state.page * state.pageSize);
    $('resultCount').textContent = state.filtered.length;
    $('jobList').innerHTML = visible.length ? visible.map(jobCard).join('') : '<div class="empty"><b>没有符合条件的岗位</b><br>尝试放宽状态、城市或方向筛选。</div>';
    $('loadMore').hidden = visible.length >= state.filtered.length;
  }
  function renderStats() {
    $('statActive').textContent = state.stats.active_jobs ?? 0; $('statNew').textContent = state.stats.new_today ?? 0; $('statHigh').textContent = state.stats.high_match ?? 0; $('statClosing').textContent = state.stats.closing_soon ?? 0;
    const stamp = state.stats.generated_at ? new Date(state.stats.generated_at) : null;
    if (stamp) $('lastUpdate').textContent = `最后更新 ${new Intl.DateTimeFormat('zh-CN',{timeZone:'Asia/Shanghai',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hour12:false}).format(stamp)} CST`;
    const cst = new Date(new Date().toLocaleString('en-US',{timeZone:'Asia/Shanghai'})); const next = cst.getHours()*60+cst.getMinutes() < 8*60+30 ? '08:30' : cst.getHours()*60+cst.getMinutes() < 20*60+30 ? '20:30' : '明日 08:30'; $('nextRadar').textContent = next;
    const entries = Object.entries(state.stats.topics || {}).slice(0,10); $('topicStats').innerHTML = entries.map(([name,count])=>`<div class="topic-stat"><b>${count}</b><span>${esc(name)}</span></div>`).join(''); $('trendStatus').textContent = state.stats.trend?.status || '样本不足';
  }

  async function initHome() {
    [state.jobs,state.stats] = await Promise.all([fetch(`${prefix}data/jobs.json`).then(r=>r.json()),fetch(`${prefix}data/stats.json`).then(r=>r.json())]);
    renderStats(); renderPriority(); populateFilters();
    ['searchInput','topicFilter','degreeFilter','typeFilter','scoreFilter','statusFilter','timeFilter','doctoralToggle','sortSelect'].forEach(id => $(id).addEventListener(id==='searchInput'?'input':'change',()=>{state.page=1;applyFilters();}));
    $('citySearch').addEventListener('input',event=>renderCities(event.target.value.trim()));
    $('resetFilters').addEventListener('click',()=>{ ['searchInput','topicFilter','degreeFilter','typeFilter'].forEach(id=>$(id).value=''); $('scoreFilter').value='0'; $('statusFilter').value='active'; $('timeFilter').value='0'; $('doctoralToggle').checked=false; state.selectedCities.clear(); renderCities(''); state.page=1; applyFilters(); });
    $('loadMore').addEventListener('click',()=>{state.page++;renderJobs();}); applyFilters();
  }
  async function initCompany() {
    state.jobs = await fetch('../data/jobs.json').then(r=>r.json()); const name = new URLSearchParams(location.search).get('name') || ''; const jobs = state.jobs.filter(job=>job.company===name); const active=jobs.filter(j=>['open','closing_soon'].includes(j.status)); const skills=[...new Set(jobs.flatMap(j=>[...(j.topics||[]),...(j.skills||[])]))].slice(0,12); const official=jobs.find(j=>j.official_apply_url)?.official_apply_url;
    document.title = `${name || '公司'}岗位｜Embodied Job Radar`; $('companyHero').innerHTML = `<div class="eyebrow">COMPANY INTELLIGENCE <span></span></div><h1>${esc(name || '未指定公司')}</h1><div class="company-summary"><span>当前岗位 ${active.length}</span><span>高匹配岗位 ${active.filter(j=>(j.match_score||0)>=80).length}</span><span>历史岗位 ${jobs.filter(j=>j.status==='expired').length}</span><span>招聘城市 ${esc([...new Set(jobs.flatMap(j=>j.city||[]))].join(' / ')||'未公开')}</span></div><div class="skill-cloud">${skills.map(x=>`<b>${esc(x)}</b>`).join('')}</div>${official?`<p><a class="apply-button" style="display:inline-block;width:auto;margin-top:28px" href="${esc(official)}" target="_blank" rel="noopener">官网招聘入口 →</a></p>`:''}`; $('companyJobCount').textContent=`共 ${jobs.length} 条记录`; $('jobList').innerHTML=jobs.length?sortJobs(jobs,'recommended').map(jobCard).join(''):'<div class="empty">暂无该公司岗位记录</div>';
  }
  async function initSources() {
    const report = await fetch('../data/update-report.json').then(r=>r.json()); const success=report.successful_sources||[], failed=report.failed_sources||[]; $('sourceReport').innerHTML = `<div class="report-row"><span>本次发现</span><b>${report.discovered_jobs ?? 0} 条</b></div><div class="report-row"><span>新增 / 更新 / 去重</span><b>${report.new_jobs ?? 0} / ${report.updated_jobs ?? 0} / ${report.duplicate_jobs ?? 0}</b></div><div class="report-row"><span>官方核验</span><b>${report.official_verified ?? 0} 条</b></div><div class="report-row"><span>成功数据源</span><b>${success.length}</b></div><div class="report-row"><span>失败数据源</span><b>${failed.length}</b></div>${failed.map(x=>`<div class="report-row"><span>${esc(x.name)}</span><b>${esc(x.error)}</b></div>`).join('')}`;
  }
  if (location.pathname.includes('/company/')) initCompany().catch(showError); else if (location.pathname.includes('/sources/')) initSources().catch(showError); else initHome().catch(showError);
  function showError(error){ console.error(error); const target=$('jobList')||$('sourceReport')||document.querySelector('main'); target.innerHTML='<div class="empty"><b>数据暂时无法读取</b><br>请稍后刷新，旧岗位数据不会因此被删除。</div>'; }
})();

