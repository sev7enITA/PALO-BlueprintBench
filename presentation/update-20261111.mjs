import path from 'node:path';
const R=path.resolve(path.dirname(new URL(import.meta.url).pathname),'..');
const brand=R+'/web/assets/blueprintbench/brand/';
export async function update({presentation,input={}}) {
 const changes=new Map([
 ['BUSINESS BLUEPRINT EVALUATION','SPECIFICATION FIDELITY RESEARCH'],
 ['Building a transparent evaluation of AI-generated business blueprints.\nResearch pilot · Actual application and configuration captures · November 2026','18 model IDs. 324 assigned internal test slots.\nReal application captures and an inspectable evidence record.\n11 November 2026. Independent qualification pending.'],
 ['Evaluation dimensions','Research dimensions'],
 ['Eight dimensions, each with a declared scope and denominator. No universal score in this pilot.','Eight proposed dimensions. Current internal tests cover a limited synthetic procurement task.'],
 ['Toolkit v0.1: 17 checks passed. It scores already-adjudicated propositions; qualification always remains false.','95 automated checks passed across evaluator, internal baseline and leaderboard tests. Human review remains open.'],
 ['Ten historical passage diagnostics. Filter properties, inspect denominators and compare observed costs and time.','18 model IDs, 28 cohort records. Internal tests and historical diagnostics retain separate denominators.'],
 ['Actual captures: 11 November 2026 · Development evidence, not independent validation','11 November 2026. Internal and development evidence. Independent qualification pending.'],
 ['Help create independent reference answers, test the business-user experience and reproduce the evidence.','Internal testing links to dated evidence. External experts are invited to establish independent reference answers.'],
 ['Bring your judgement','Independent review'],
 ['Process annotators\nBusiness participants\nTechnical reproducers\nCorpus contributors','Procurement annotators\nExternal custodian\nTechnical reproducer\n\nNo PBI assigned.'],
 ['Proposed summary, not yet scored. Freeze the method and obtain independent evidence before assigning an index.','Proposed index. Independent gold, external custody and validation of the measure remain open.'],
 ['Existing repositories are development cases used to repair PALO. They cannot qualify an unseen-case ranking.','Earlier development runs, retained for context. The new 18-model tests use short synthetic cases.']
 ]);
 for(let i=input.start??0;i<(input.end??presentation.slides.items.length);i++){
  const s=presentation.slides.getItem(i);
  for(const sh of s.shapes.items){const t=sh.text.toString();if(changes.has(t))sh.text=changes.get(t);if(t.startsWith('Building a transparent evaluation of AI-generated business blueprints.'))sh.text='18 model IDs. 324 assigned internal test slots.\nReal application captures and an inspectable evidence record.\n11 November 2026. Independent qualification pending.';if(t==='PALO BLUEPRINTBENCH / RESEARCH PILOT')sh.position.width=850;}
  if(!s.images.items.some(im=>im.alt==='Original PALO Framework logo')) s.images.add({path:brand+'palo-framework-logo.png',alt:'Original PALO Framework logo',position:{left:1170,top:12,width:60,height:60},fit:'contain'});
  if(i>0&&!s.images.items.some(im=>im.alt==='BlueprintBench identity'))s.images.add({path:brand+'blueprintbench-logo.jpg',alt:'BlueprintBench identity',position:{left:966,top:12,width:186,height:62},fit:'contain'});
 }
 if((input.start??0)===0){const cover=presentation.slides.getItem(0);for(const sh of cover.shapes.items){if(sh.text.toString()==='PALO\nBlueprintBench')sh.text='';}
 if(!cover.images.items.some(im=>im.alt==='BlueprintBench identity'))cover.images.add({path:brand+'blueprintbench-logo.jpg',alt:'BlueprintBench identity',position:{left:60,top:180,width:1120,height:260},fit:'contain'});
 }
 if((input.start??0)<=13&&(input.end??15)>13){const comparison=presentation.slides.getItem(13);await comparison.images.items[0].replace({path:R+'/presentation/screenshots/18-internal-leaderboard.png'});comparison.images.items[0].alt='Actual updated internal procurement leaderboard, 11 November 2026';
 for(const sh of comparison.shapes.items){if(sh.text.toString().startsWith('11 November 2026. Internal')){sh.text='324 assigned: 299 complete, 7 failed/incomplete, 18 pre-call blocked. 306 requests dispatched.';sh.text.style={fontSize:16,color:'#b7c8d8'};}}
 }
 if((input.end??15)===15){const last=presentation.slides.getItem(14);await last.images.items[0].replace({path:brand+'internal-testing-badge.jpg'});last.images.items[0].alt='BlueprintBench Internal testing badge, evidence linked. Not certification.';last.images.items[0].position={left:170,top:205,width:430,height:430};
 }
 return {slides:presentation.slides.items.length,revision:'brand-and-expanded-internal-cohort-2026-11-11'};
}
