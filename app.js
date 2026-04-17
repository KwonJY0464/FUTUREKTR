window.allData = null;
window.currentMode = 'news';
window.currentCalDate = new Date(); // 💡 달력 월 추적용 변수

document.addEventListener('DOMContentLoaded', () => {
    const resizer = document.getElementById('resizer');
    let isResizing = false;
    if (resizer) {
        resizer.addEventListener('mousedown', () => { isResizing = true; });
        document.addEventListener('mousemove', (e) => {
            if (!isResizing) return;
            const x = e.clientX;
            if (x > 300 && x < window.innerWidth - 350) {
                document.documentElement.style.setProperty('--left-width', `${x}px`);
            }
        });
        document.addEventListener('mouseup', () => { isResizing = false; });
    }
    
    switchMode('news');
});

window.toggleTheme = function() {
    const b = document.body; 
    const isDark = b.getAttribute('data-theme') === 'dark';
    b.setAttribute('data-theme', isDark ? 'light' : 'dark');
    document.getElementById('themeIcon').innerText = isDark ? '🌙' : '☀️';
};

window.switchMode = async function(mode) {
    window.currentMode = mode;
    document.querySelectorAll('.mode-btn').forEach(btn => btn.classList.remove('active'));
    
    const activeBtn = document.getElementById(`mode-${mode}`);
    if(activeBtn) activeBtn.classList.add('active');
    
    const newsLeft = document.getElementById('news-left-pane');
    const assemblyLeft = document.getElementById('assembly-left-pane');

    if (mode === 'news') {
        if(newsLeft) newsLeft.style.display = 'flex';
        if(assemblyLeft) assemblyLeft.style.display = 'none';
        await loadNewsData();
    } else {
        if(newsLeft) newsLeft.style.display = 'none';
        if(assemblyLeft) assemblyLeft.style.display = 'flex';
        // 달력을 열때마다 현재 달로 초기화
        window.currentCalDate = new Date(); 
        await loadAssemblyData();
    }
};

async function loadNewsData() {
    try {
        const title1 = document.getElementById('pane1-title');
        if(title1) title1.innerText = "인기뉴스";
        
        const title2 = document.getElementById('pane2-title');
        if(title2) title2.innerHTML = '부처/기관 <span id="pane2-tabs"></span>';
        
        const title3 = document.getElementById('pane3-title');
        if(title3) title3.innerHTML = 'AI 키워드 타게팅 <span id="pane3-tabs"></span>';
        
        const res = await fetch(`news.json?t=${Date.now()}`); 
        if (!res.ok) throw new Error("news.json load failed");
        window.allData = await res.json();
        
        renderItems('pane1-content', window.allData.pane1);
        
        ['pane2', 'pane3'].forEach(id => {
            if (!window.allData[id]) return;
            const n = id.slice(-1); 
            const kws = Object.keys(window.allData[id]);
            const t = document.getElementById(`pane${n}-tabs`);
            if(t && kws.length > 0) {
                t.innerHTML = kws.map((kw, i) => `<button class="tab-btn ${i===0?'active':''}" onclick="switchTab(${n},'${kw}',this)">${kw}</button>`).join('');
                switchTab(n, kws[0], t.firstChild);
            }
        });
        
        const timeStr = window.allData.last_updated ? window.allData.last_updated.substring(11, 16) : '';
        const ts = `업데이트: ${timeStr}`;
        ['time-1-news', 'time-2', 'time-3'].forEach(id => {
            const el = document.getElementById(id);
            if(el) el.innerText = ts;
        });
    } catch (e) {
        console.error("News Load Error:", e);
        const content1 = document.getElementById('pane1-content');
        if(content1) content1.innerHTML = "<div style='padding:20px; color:#999;'>데이터를 불러올 수 없습니다.</div>";
    }
}

async function loadAssemblyData() {
    try {
        const title2 = document.getElementById('pane2-title');
        if(title2) title2.innerText = "입법/정책 동향";
        
        const title3 = document.getElementById('pane3-title');
        if(title3) title3.innerText = "AI 요약";
        
        const t2 = document.getElementById('pane2-tabs'); if(t2) t2.innerHTML = '';
        const t3 = document.getElementById('pane3-tabs'); if(t3) t3.innerHTML = '';

        const res = await fetch(`assembly.json?t=${Date.now()}`);
        if (!res.ok) throw new Error("assembly.json load failed");
        const data = await res.json();
        window.allData = data; 
        
        if(data.schedules) {
            renderSingleCalendar(data.schedules);
        }
        
        const content2 = document.getElementById('pane2-content');
        if(content2) content2.innerHTML = `<div style="padding:40px; text-align:center; opacity:0.4;">의안 데이터 API 연동 대기 중</div>`;
        
        const content3 = document.getElementById('pane3-content');
        if(content3) content3.innerHTML = `<div style="padding:20px; line-height:1.8;">${data.summary ? data.summary.replace(/\n/g, '<br>') : '요약 정보가 없습니다.'}</div>`;
        
        const timeStr = data.last_updated ? data.last_updated.substring(11, 16) : '';
        const ts = `업데이트: ${timeStr}`;
        ['time-1-assembly', 'time-2', 'time-3'].forEach(id => {
            const el = document.getElementById(id);
            if(el) el.innerText = ts;
        });
    } catch (e) { 
        console.error("Assembly Load Error:", e);
        const contentAssm = document.getElementById('pane1-assembly-content');
        if(contentAssm) contentAssm.innerHTML = `<div style="padding:40px; text-align:center; color:#999;">국회 데이터를 불러올 수 없습니다.</div>`;
    }
}

// 💡 월 변경 함수
window.changeMonth = function(offset) {
    window.currentCalDate.setMonth(window.currentCalDate.getMonth() + offset);
    if(window.allData && window.allData.schedules) {
        renderSingleCalendar(window.allData.schedules);
    }
};

// 💡 단일 달력 렌더링 함수
function renderSingleCalendar(schedules) {
    const wrapper = document.getElementById('calendar-wrapper');
    if(!wrapper) return;
    
    const year = window.currentCalDate.getFullYear();
    const month = window.currentCalDate.getMonth();
    
    wrapper.innerHTML = `<div class="single-calendar">
        ${generateSingleMonthHTML(year, month, schedules)}
    </div>`;
}

function generateSingleMonthHTML(year, month, schedules) {
    const days = ['일','월','화','수','목','금','토'];
    const firstDay = new Date(year, month, 1).getDay();
    const lastDate = new Date(year, month + 1, 0).getDate();
    
    let html = `
        <div class="cal-header">
            <button class="cal-nav-btn" onclick="changeMonth(-1)">&#10094;</button>
            <span>${year}년 ${month+1}월 국회 상황판</span>
            <button class="cal-nav-btn" onclick="changeMonth(1)">&#10095;</button>
        </div>
        <div class="cal-grid">${days.map(d => `<div style="color:#999; padding-bottom:10px;">${d}</div>`).join('')}`;
    
    for(let i=0; i<firstDay; i++) html += `<div></div>`;
    
    const todayStr = new Date().toISOString().split('T')[0];

    for(let d=1; d<=lastDate; d++) {
        const dateStr = `${year}-${String(month+1).padStart(2,'0')}-${String(d).padStart(2,'0')}`;
        const hasSanja = schedules.some(s => s.date === dateStr && s.type === 'sanja');
        const hasGihyu = schedules.some(s => s.date === dateStr && s.type === 'gihyu');
        const isToday = (todayStr === dateStr);
        
        html += `<div class="cal-day ${isToday?'today':''}" onclick="selectDate('${dateStr}', this)">
            ${d}
            <div style="height:6px; margin-top:4px;">
                ${hasSanja ? '<span class="cal-dot dot-sanja"></span>' : ''}
                ${hasGihyu ? '<span class="cal-dot dot-gihyu"></span>' : ''}
            </div>
        </div>`;
    }
    return html + `</div>`;
}

window.selectDate = function(date, el) {
    document.querySelectorAll('.cal-day').forEach(d => d.classList.remove('selected'));
    if(el) el.classList.add('selected');
    
    if(window.allData && window.allData.schedules) {
        const daySchedules = window.allData.schedules.filter(s => s.date === date);
        renderItems('pane1-assembly-content', daySchedules);
    }
};

function renderItems(targetId, items) {
    const container = document.getElementById(targetId);
    if(!container) return;
    
    if (!items || items.length === 0) {
        container.innerHTML = `<div style="padding:40px; text-align:center; color:#999;">해당 항목에 일정이 없습니다.</div>`;
        return;
    }
    
    container.innerHTML = items.map(item => {
        let dot = "";
        if(window.currentMode === 'assembly' && item.type !== 'session') {
            const dotColor = item.type === 'sanja' ? 'var(--sanja-color)' : 'var(--gihyu-color)';
            dot = `<div class="type-dot" style="background:${dotColor}"></div>`;
        }
        
        const titleText = item.title ? item.title.replace(/<[^>]*>?/gm, '') : '제목 없음';
        const summaryText = item.ai_summary ? `<p>${item.ai_summary}</p>` : '';
        const metaText = item.formatted_date || (item.time + ' | ' + (item.committee||'') + ' | ' + (item.location || '장소미정'));
        
        return `
        <div class="item" onclick="if('${item.link||''}') window.open('${item.link}', '_blank')">
            <h3>${dot}${titleText}</h3>
            ${summaryText}
            <span class="meta">${metaText}</span>
        </div>`;
    }).join('');
}

window.switchTab = function(p, kw, btn) {
    document.querySelectorAll(`#pane${p}-tabs .tab-btn`).forEach(b => b.classList.remove('active'));
    if(btn) btn.classList.add('active'); 
    if(window.allData && window.allData[`pane${p}`]) {
        renderItems(`pane${p}-content`, window.allData[`pane${p}`][kw]);
    }
};
