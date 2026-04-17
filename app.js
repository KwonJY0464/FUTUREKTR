let allData = null;
let currentMode = 'news';
let selectedDate = null;

const resizer = document.getElementById('resizer');
if (resizer) {
    resizer.addEventListener('mousedown', () => {
        document.addEventListener('mousemove', handleResizing);
        document.addEventListener('mouseup', () => document.removeEventListener('mousemove', handleResizing));
    });
}

function handleResizing(e) {
    const x = e.clientX;
    if (x > 300 && x < window.innerWidth - 350) {
        document.documentElement.style.setProperty('--left-width', `${x}px`);
    }
}

function toggleTheme() {
    const b = document.body; const isDark = b.getAttribute('data-theme') === 'dark';
    b.setAttribute('data-theme', isDark ? 'light' : 'dark');
    document.getElementById('themeIcon').innerText = isDark ? '🌙' : '☀️';
}

async function switchMode(mode) {
    currentMode = mode;
    document.querySelectorAll('.mode-btn').forEach(btn => btn.classList.remove('active'));
    document.getElementById(`mode-${mode}`).classList.add('active');
    
    const container = document.getElementById('left-container');
    if (mode === 'news') {
        container.innerHTML = `
            <div class="pane" style="height:100%">
                <div class="pane-header"><div id="pane1-title">인기뉴스</div> <span id="time-1"></span></div>
                <div id="pane1-content" class="scroll-content"></div>
            </div>`;
        await loadNewsData();
    } else {
        container.innerHTML = `
            <div class="pane" style="height: 45%; flex-shrink: 0;">
                <div class="pane-header"><div>국회 상황판 (이번달 + 다음달)</div></div>
                <div id="calendar-wrapper" class="scroll-content"></div>
            </div>
            <div class="pane" style="flex: 1;">
                <div class="pane-header"><div>핵심 의사일정 상세</div> <span id="time-1"></span></div>
                <div id="pane1-content" class="scroll-content">
                    <div style="padding:40px; text-align:center; color:#999;">날짜를 선택해주세요.</div>
                </div>
            </div>`;
        await loadAssemblyData();
    }
}

async function loadNewsData() {
    try {
        const res = await fetch(`news.json?t=${Date.now()}`);
        allData = await res.json();
        renderItems('pane1-content', allData.pane1);
        updateTimestamps(allData.last_updated);
        // 뉴스 탭 렌더링 로직 (생략 - 기존 유지)
    } catch (e) { console.error(e); }
}

async function loadAssemblyData() {
    try {
        const res = await fetch(`assembly.json?t=${Date.now()}`);
        const data = await res.json();
        allData = data; // 전역 저장
        renderDualCalendar(data.schedules);
        document.getElementById('pane2-title').innerText = "입법/정책 동향";
        document.getElementById('pane3-title').innerText = "AI 요약";
        document.getElementById('pane2-content').innerHTML = `<div style="padding:40px; text-align:center; opacity:0.4;">의안 데이터 API 연동 대기 중</div>`;
        document.getElementById('pane3-content').innerHTML = `<div style="padding:20px; line-height:1.8;">${data.summary.replace(/\n/g, '<br>')}</div>`;
        updateTimestamps(data.last_updated);
    } catch (e) { console.error(e); }
}

function renderDualCalendar(schedules) {
    const wrapper = document.getElementById('calendar-wrapper');
    const now = new Date();
    const next = new Date(now.getFullYear(), now.getMonth() + 1, 1);
    
    wrapper.innerHTML = `<div class="dual-calendar">
        ${generateMonthHTML(now.getFullYear(), now.getMonth(), schedules)}
        ${generateMonthHTML(next.getFullYear(), next.getMonth(), schedules)}
    </div>`;
}

function generateMonthHTML(year, month, schedules) {
    const days = ['일','월','화','수','목','금','토'];
    const firstDay = new Date(year, month, 1).getDay();
    const lastDate = new Date(year, month + 1, 0).getDate();
    
    let html = `<div class="cal-month">
        <div style="text-align:center; font-weight:bold; margin-bottom:8px;">${year}년 ${month+1}월</div>
        <div class="cal-grid">${days.map(d => `<div style="color:#999">${d}</div>`).join('')}`;
    
    for(let i=0; i<firstDay; i++) html += `<div></div>`;
    for(let d=1; d<=lastDate; d++) {
        const dateStr = `${year}-${String(month+1).padStart(2,'0')}-${String(d).padStart(2,'0')}`;
        const hasSanja = schedules.some(s => s.date === dateStr && s.type === 'sanja');
        const hasGihyu = schedules.some(s => s.date === dateStr && s.type === 'gihyu');
        const isToday = new Date().toISOString().split('T')[0] === dateStr;
        
        html += `<div class="cal-day ${isToday?'today':''}" onclick="selectDate('${dateStr}', this)">
            ${d}
            <div style="height:4px;">
                ${hasSanja ? '<span class="cal-dot dot-sanja"></span>' : ''}
                ${hasGihyu ? '<span class="cal-dot dot-gihyu"></span>' : ''}
            </div>
        </div>`;
    }
    return html + `</div></div>`;
}

function selectDate(date, el) {
    document.querySelectorAll('.cal-day').forEach(d => d.classList.remove('selected'));
    el.classList.add('selected');
    
    const daySchedules = allData.schedules.filter(s => s.date === date);
    renderItems('pane1-content', daySchedules);
}

function renderItems(targetId, items) {
    const container = document.getElementById(targetId);
    if (!items || items.length === 0) {
        container.innerHTML = `<div style="padding:40px; text-align:center; color:#999;">해당 날짜에 일정이 없습니다.</div>`;
        return;
    }
    container.innerHTML = items.map(item => {
        const dotColor = item.type === 'sanja' ? 'var(--sanja-color)' : (item.type === 'gihyu' ? 'var(--gihyu-color)' : 'transparent');
        const dot = item.type !== 'session' ? `<div class="type-dot" style="background:${dotColor}"></div>` : '';
        return `<div class="item">
            <h3>${dot}${item.title}</h3>
            <p style="font-size:0.85rem; color:#888;">${item.time} | ${item.committee} | ${item.location || '장소미정'}</p>
        </div>`;
    }).join('');
}

function updateTimestamps(ts) {
    const time = ts ? ts.substring(11, 16) : '--:--';
    ['1','2','3'].forEach(n => {
        const el = document.getElementById(`time-${n}`);
        if(el) el.innerText = `업데이트: ${time}`;
    });
}

switchMode('news');
