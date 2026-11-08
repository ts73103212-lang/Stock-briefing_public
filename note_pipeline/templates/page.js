// 初回有料記事（中間選挙）の納品ページから移植。記事ごとのコピーに対応。
(function(){
function say(el,t){if(!el)return;el.textContent=t;setTimeout(function(){el.textContent=''},2500)}
function fallbackSelect(el,st){var r=document.createRange();r.selectNodeContents(el);var s=getSelection();s.removeAllRanges();s.addRange(r);say(st,'選択しました。コピー操作をしてください')}
document.querySelectorAll('[data-copy]').forEach(function(b){b.addEventListener('click',function(){
  var el=document.getElementById(b.dataset.copy);
  navigator.clipboard.writeText(el.innerText).then(function(){b.textContent='コピー済み';setTimeout(function(){b.textContent='コピー'},1500)}).catch(function(){fallbackSelect(el)});
})});
function bodyClone(id){
  var c=document.getElementById(id).cloneNode(true);
  c.querySelectorAll('figure').forEach(function(f){f.remove()});
  c.querySelectorAll('.paywall').forEach(function(p){var q=document.createElement('p');q.textContent='――――（ここから有料）――――';p.replaceWith(q)});
  return c;
}
function textOf(c){c.style.cssText='position:absolute;left:-9999px;top:0;width:700px';document.body.appendChild(c);var t=c.innerText;c.remove();c.style.cssText='';return t}
document.querySelectorAll('[data-copy-body]').forEach(function(b){b.addEventListener('click',function(){
  var id=b.dataset.copyBody, st=document.getElementById(b.dataset.status), src=document.getElementById(id);
  var c=bodyClone(id), html=c.innerHTML, txt=textOf(c);
  function plain(){navigator.clipboard.writeText(txt).then(function(){say(st,'テキストでコピーしました')}).catch(function(){fallbackSelect(src,st)})}
  try{
    var item=new ClipboardItem({'text/html':new Blob([html],{type:'text/html'}),'text/plain':new Blob([txt],{type:'text/plain'})});
    navigator.clipboard.write([item]).then(function(){say(st,'本文をコピーしました（図の位置は［図○］）')}).catch(plain);
  }catch(e){plain()}
})});
document.querySelectorAll('[data-copy-plain]').forEach(function(b){b.addEventListener('click',function(){
  var id=b.dataset.copyPlain, st=document.getElementById(b.dataset.status);
  var t=textOf(bodyClone(id));
  navigator.clipboard.writeText(t).then(function(){say(st,'プレーンテキストでコピーしました')}).catch(function(){fallbackSelect(document.getElementById(id),st)});
})});
})();
