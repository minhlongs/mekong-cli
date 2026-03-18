const API = 'https://mekong-engine.agencyos-openclaw.workers.dev';
let step = 0;
const state = { industry:'', name:'', address:'', phone:'', hours:'', channel:'zalo', channelId:'', channelToken:'', menu:[] };

function apiKey() { return localStorage.getItem('mk_api_key'); }
function post(path, body) {
  return fetch(API + path, { method:'POST', headers:{'Content-Type':'application/json','Authorization':'Bearer '+apiKey()}, body: JSON.stringify(body) }).catch(()=>{});
}

export function goTo(s) {
  document.getElementById('step-'+step).classList.remove('active');
  document.getElementById('dot-'+step).classList.remove('active');
  document.getElementById('dot-'+step).classList.add('done');
  step = s;
  document.getElementById('step-'+step).classList.add('active');
  document.getElementById('dot-'+step).classList.add('active');
}

export function initIndustry() {
  document.querySelectorAll('.industry-btn').forEach(btn => btn.addEventListener('click', () => {
    document.querySelectorAll('.industry-btn').forEach(b => b.classList.remove('selected'));
    btn.classList.add('selected');
    state.industry = btn.dataset.v;
  }));
  document.getElementById('next-0').addEventListener('click', () => {
    if (!state.industry) { document.getElementById('err-0').style.display='block'; return; }
    document.getElementById('err-0').style.display='none';
    goTo(1);
  });
}

export function initBizInfo() {
  document.getElementById('back-1').addEventListener('click', () => goTo(0));
  document.getElementById('next-1').addEventListener('click', async () => {
    state.name = document.getElementById('biz-name').value.trim();
    if (!state.name) { document.getElementById('err-1').style.display='block'; return; }
    document.getElementById('err-1').style.display='none';
    state.address = document.getElementById('biz-address').value.trim();
    state.phone   = document.getElementById('biz-phone').value.trim();
    state.hours   = document.getElementById('biz-hours').value.trim();
    await post('/v1/onboard/business', { industry:state.industry, name:state.name, address:state.address, phone:state.phone, hours:state.hours });
    goTo(2);
  });
}

export function initChannel() {
  document.querySelectorAll('input[name=channel]').forEach(r => r.addEventListener('change', e => {
    state.channel = e.target.value;
    document.getElementById('zalo-fields').style.display = state.channel==='zalo' ? 'block' : 'none';
    document.getElementById('fb-fields').style.display   = state.channel==='facebook' ? 'block' : 'none';
  }));
  document.getElementById('back-2').addEventListener('click', () => goTo(1));
  document.getElementById('next-2').addEventListener('click', async () => {
    state.channelId    = state.channel==='zalo' ? document.getElementById('zalo-oa-id').value.trim() : document.getElementById('fb-page-id').value.trim();
    state.channelToken = state.channel==='zalo' ? document.getElementById('zalo-token').value.trim()  : document.getElementById('fb-token').value.trim();
    await post('/v1/onboard/channel', { platform:state.channel, page_id:state.channelId, token:state.channelToken });
    goTo(3);
  });
}

export function initMenu() {
  function render() {
    const list = document.getElementById('menu-list');
    list.innerHTML = state.menu.map((item,i) => `<div class="menu-item"><input value="${item.name}" placeholder="Tên món/dịch vụ" data-i="${i}" data-f="name"/><input value="${item.price}" placeholder="Giá (VD: 50.000đ)" data-i="${i}" data-f="price" style="max-width:140px"/><button class="btn btn-secondary btn-sm" data-remove="${i}">✕</button></div>`).join('');
    list.querySelectorAll('input').forEach(inp => inp.addEventListener('input', e => { state.menu[e.target.dataset.i][e.target.dataset.f]=e.target.value; }));
    list.querySelectorAll('[data-remove]').forEach(btn => btn.addEventListener('click', e => { state.menu.splice(+e.target.dataset.remove,1); render(); }));
  }
  document.getElementById('add-item').addEventListener('click', () => { state.menu.push({name:'',price:''}); render(); });
  document.getElementById('back-3').addEventListener('click', () => goTo(2));
  document.getElementById('next-3').addEventListener('click', async () => {
    await post('/v1/onboard/menu', { items: state.menu.filter(m=>m.name) });
    document.getElementById('confirm-biz-name').textContent = state.name || 'doanh nghiệp';
    goTo(4);
  });
}

export function initActivate() {
  document.getElementById('back-4').addEventListener('click', () => goTo(3));
  document.getElementById('btn-activate').addEventListener('click', async () => {
    const btn = document.getElementById('btn-activate');
    btn.textContent='Đang kích hoạt...'; btn.disabled=true;
    try {
      const res = await fetch(API+'/v1/onboard/activate', {method:'POST',headers:{'Content-Type':'application/json','Authorization':'Bearer '+apiKey()},body:'{}'});
      if (!res.ok) throw new Error();
      localStorage.setItem('mk_biz_name', state.name);
      window.location.href='/dashboard';
    } catch {
      document.getElementById('err-4').style.display='block';
      btn.textContent='⚡ Kích hoạt AI ngay'; btn.disabled=false;
    }
  });
}
