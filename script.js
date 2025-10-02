async function loadRules(){
  const resp = await fetch('../output/rules.json');
  const data = await resp.json();
  const rules = data.sections || [];
  const container = document.getElementById('rules');
  container.innerHTML = '';
  rules.forEach(rule=>{
    const div = document.createElement('div');
    div.className = 'rule';
    div.innerHTML = `
      <h2 id="${rule.id}">${escapeHtml(rule.title)}</h2>
      <small>Start page: ${rule.start_page || 'n/a'}</small>
      <hr>
      <pre>${escapeHtml(rule.content)}</pre>
    `;
    container.appendChild(div);
  });
}

function escapeHtml(s){
  return String(s).replace(/[&<>"']/g, m => (
    {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]
  ));
}

loadRules().catch(err=>{
  document.getElementById('rules').innerHTML =
    '<p style="color:red">Error loading rules.json: '+err+'</p>';
});
