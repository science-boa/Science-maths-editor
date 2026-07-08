<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Maths for Science</title>
  
  <script src="https://cdn.tailwindcss.com"></script>
  
  <script src="https://cdnjs.cloudflare.com/ajax/libs/js-yaml/4.1.0/js-yaml.min.js"></script>
  
  <script src="https://cdnjs.cloudflare.com/ajax/libs/mathjs/12.4.1/math.js"></script>
  
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
  <script src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js"></script>

  <style>
    input::-webkit-outer-spin-button,
    input::-webkit-inner-spin-button {
      -webkit-appearance: none;
      margin: 0;
    }
    input[type=number] {
      -moz-appearance: textfield;
    }
  </style>
</head>
<body class="bg-gray-50 min-h-screen text-gray-800 antialiased font-sans">

  <div class="max-w-7xl mx-auto px-4 py-8">
    <header class="mb-8 border-b border-gray-200 pb-4 flex justify-between items-center">
      <h1 class="text-3xl font-bold text-gray-900 tracking-tight">Maths for Science</h1>
      <span id="loading-badge" class="bg-amber-100 text-amber-800 text-xs font-semibold px-3 py-1 rounded-full animate-pulse">Loading Questions...</span>
    </header>

    <div id="dashboard" class="flex gap-2 mb-6 overflow-x-auto pb-2"></div>

    <div id="quiz-workspace" class="grid grid-cols-1 lg:grid-cols-3 gap-8">
      
      <div class="lg:col-span-2 space-y-6">
        
        <div class="bg-white p-6 rounded-xl shadow-sm border border-gray-200 space-y-6">
          <div id="question-area">
            <div class="text-gray-400 text-center py-16">Awaiting URL parameters...</div>
          </div>

          <div id="working-area" class="pt-4 border-t border-gray-100 hidden">
            <h3 class="text-xs font-bold uppercase tracking-wider text-gray-500 mb-2">Working</h3>
            <textarea id="scratchpad" oninput="saveScratchpad()" placeholder="Type your equations, formulas, and numeric calculations here..." class="w-full h-44 p-3 font-mono text-sm border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none resize-none bg-amber-50/30"></textarea>
          </div>

          <div id="answer-area" class="pt-4 border-t border-gray-100 hidden">
            <div class="flex items-center gap-4">
              <label class="font-semibold text-gray-700 shrink-0">Your Answer:</label>
              <input type="number" id="answer-input" step="any" oninput="captureAnswer(this.value)" placeholder="Enter numeric value" class="border border-gray-300 rounded-lg px-3 py-2 w-48 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none font-mono">
            </div>
          </div>
        </div>

        <div class="flex justify-between items-center pt-2">
          <button id="btn-prev" onclick="changeQuestion(-1)" class="px-5 py-2 bg-gray-200 hover:bg-gray-300 disabled:opacity-40 font-medium rounded-lg transition-colors cursor-pointer" disabled>
            ← Previous
          </button>
          <button id="btn-next" onclick="changeQuestion(1)" class="px-5 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors cursor-pointer">
            Next →
          </button>
          <button id="btn-submit" onclick="submitQuiz()" class="px-6 py-2 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-lg transition-colors hidden cursor-pointer">
            Submit Quiz
          </button>
        </div>
      </div>

      <div class="space-y-6">
        <div class="bg-slate-900 text-white p-4 rounded-2xl shadow-xl border border-slate-800 w-full max-w-sm mx-auto">
          <div class="flex justify-between items-center mb-1 text-[10px] uppercase font-bold tracking-wider text-slate-400 px-1">
            <span>GCSE Scientific</span>
            <span class="text-emerald-400 font-mono">DEG MODE</span>
          </div>
          
          <div class="bg-slate-950 border border-slate-800 rounded-xl p-3 mb-4 text-right font-mono min-h-[72px] flex flex-col justify-between">
            <div id="calc-history" class="text-xs text-slate-500 overflow-hidden text-ellipsis whitespace-nowrap"></div>
            <div id="calc-display" class="text-xl text-emerald-400 font-semibold overflow-x-auto whitespace-nowrap">0</div>
          </div>
          
          <div class="grid grid-cols-5 gap-1.5 text-xs font-bold">
            <button onclick="pressCalc('sin(')" class="bg-slate-800 hover:bg-slate-700 p-2.5 rounded-lg text-slate-300 cursor-pointer">sin</button>
            <button onclick="pressCalc('cos(')" class="bg-slate-800 hover:bg-slate-700 p-2.5 rounded-lg text-slate-300 cursor-pointer">cos</button>
            <button onclick="pressCalc('tan(')" class="bg-slate-800 hover:bg-slate-700 p-2.5 rounded-lg text-slate-300 cursor-pointer">tan</button>
            <button onclick="pressCalc('(')" class="bg-slate-700 hover:bg-slate-600 p-2.5 rounded-lg text-slate-200 cursor-pointer">(</button>
            <button onclick="pressCalc(')')" class="bg-slate-700 hover:bg-slate-600 p-2.5 rounded-lg text-slate-200 cursor-pointer">)</button>

            <button onclick="pressCalc('sqrt(')" class="bg-slate-800 hover:bg-slate-700 p-2.5 rounded-lg text-slate-300 cursor-pointer">√</button>
            <button onclick="pressCalc('^2')" class="bg-slate-800 hover:bg-slate-700 p-2.5 rounded-lg text-slate-300 cursor-pointer">x²</button>
            <button onclick="pressCalc('^')" class="bg-slate-800 hover:bg-slate-700 p-2.5 rounded-lg text-slate-300 cursor-pointer">xʸ</button>
            <button onclick="pressCalc('pi')" class="bg-slate-800 hover:bg-slate-700 p-2.5 rounded-lg text-slate-300 cursor-pointer">π</button>
            <button onclick="pressCalc('*10^')" class="bg-slate-800 hover:bg-slate-700 p-2.5 rounded-lg text-slate-300 cursor-pointer">EXP</button>

            <button onclick="pressCalc('7')" class="bg-slate-700 hover:bg-slate-600 p-3 rounded-lg text-lg cursor-pointer">7</button>
            <button onclick="pressCalc('8')" class="bg-slate-700 hover:bg-slate-600 p-3 rounded-lg text-lg cursor-pointer">8</button>
            <button onclick="pressCalc('9')" class="bg-slate-700 hover:bg-slate-600 p-3 rounded-lg text-lg cursor-pointer">9</button>
            <button onclick="pressCalc('DEL')" class="bg-amber-600 hover:bg-amber-500 p-3 rounded-lg text-white font-extrabold cursor-pointer">DEL</button>
            <button onclick="pressCalc('AC')" class="bg-rose-700 hover:bg-rose-600 p-3 rounded-lg text-white font-extrabold cursor-pointer">AC</button>

            <button onclick="pressCalc('4')" class="bg-slate-700 hover:bg-slate-600 p-3 rounded-lg text-lg cursor-pointer">4</button>
            <button onclick="pressCalc('5')" class="bg-slate-700 hover:bg-slate-600 p-3 rounded-lg text-lg cursor-pointer">5</button>
            <button onclick="pressCalc('6')" class="bg-slate-700 hover:bg-slate-600 p-3 rounded-lg text-lg cursor-pointer">6</button>
            <button onclick="pressCalc('*')" class="bg-slate-800 hover:bg-slate-700 p-3 rounded-lg text-base text-slate-300 cursor-pointer">×</button>
            <button onclick="pressCalc('/')" class="bg-slate-800 hover:bg-slate-700 p-3 rounded-lg text-base text-slate-300 cursor-pointer">÷</button>

            <button onclick="pressCalc('1')" class="bg-slate-700 hover:bg-slate-600 p-3 rounded-lg text-lg cursor-pointer">1</button>
            <button onclick="pressCalc('2')" class="bg-slate-700 hover:bg-slate-600 p-3 rounded-lg text-lg cursor-pointer">2</button>
            <button onclick="pressCalc('3')" class="bg-slate-700 hover:bg-slate-600 p-3 rounded-lg text-lg cursor-pointer">3</button>
            <button onclick="pressCalc('+')" class="bg-slate-800 hover:bg-slate-700 p-3 rounded-lg text-base text-slate-300 cursor-pointer">+</button>
            <button onclick="pressCalc('-')" class="bg-slate-800 hover:bg-slate-700 p-3 rounded-lg text-base text-slate-300 cursor-pointer">-</button>

            <button onclick="pressCalc('0')" class="bg-slate-700 hover:bg-slate-600 p-3 rounded-lg text-lg cursor-pointer">0</button>
            <button onclick="pressCalc('.')" class="bg-slate-700 hover:bg-slate-600 p-3 rounded-lg text-lg cursor-pointer">.</button>
            <button onclick="pressCalc('Ans')" class="bg-slate-800 hover:bg-slate-700 p-3 rounded-lg text-slate-300 cursor-pointer">Ans</button>
            <button onclick="pressCalc('=')" class="bg-emerald-600 hover:bg-emerald-500 p-3 rounded-lg text-white font-bold col-span-2 text-base shadow-lg cursor-pointer">=</button>
          </div>
        </div>
      </div>
    </div>

    <div id="quiz-results-screen" class="hidden max-w-4xl mx-auto space-y-8 pb-12">
      <div class="bg-gradient-to-r from-emerald-600 to-teal-700 text-white p-8 rounded-2xl shadow-md text-center">
        <h2 class="text-3xl font-extrabold tracking-tight">Quiz Complete!</h2>
        <p class="text-emerald-100 mt-2 text-lg font-medium">Here is your step-by-step breakdown.</p>
        <div class="mt-4 inline-block bg-white/20 backdrop-blur-md px-6 py-2 rounded-full font-mono text-2xl font-bold">
          Total Score: <span id="results-score-badge">0 / 0</span>
        </div>
      </div>
      
      <div id="results-cards-container" class="space-y-6"></div>
      
      <div class="text-center">
        <button onclick="location.reload()" class="px-6 py-3 bg-gray-800 hover:bg-gray-900 text-white font-bold rounded-lg transition-colors">
          Start Over
        </button>
      </div>
    </div>

  </div>

  <script>
    const BASE_RAW_URL = "https://raw.githubusercontent.com/science-boa/Science-maths-editor/main/Q/";
    let questions = [];
    let currentIndex = 0;
    let studentAnswers = {};
    
    let calcExpression = "";
    let lastAnswer = 0;

    // 1. App initialization
    window.addEventListener('DOMContentLoaded', async () => {
      const params = new URLSearchParams(window.location.search);
      const qKeys = Array.from(params.keys()).filter(k => k.startsWith('q')).sort();

      if (qKeys.length === 0) {
        document.getElementById('question-area').innerHTML = `
          <div class="text-center py-12">
            <p class="text-red-500 font-semibold text-lg">No configuration payload detected.</p>
            <p class="text-sm text-gray-500 mt-2">Append target files to your browser window address bar string: <code class="bg-gray-100 p-1 rounded font-mono text-xs">?q1=PHYS-2026-001</code></p>
          </div>`;
        document.getElementById('loading-badge').classList.add('hidden');
        return;
      }

      for (const key of qKeys) {
        const fileId = params.get(key);
        if (!fileId) continue;
        try {
          const response = await fetch(`${BASE_RAW_URL}${fileId}.yaml`);
          if (!response.ok) throw new Error(`Status ${response.status}`);
          const text = await response.text();
          const parsed = jsyaml.load(text);
          questions.push({ ...parsed, id: fileId });
        } catch (err) {
          questions.push({ id: fileId, error: true, message: `Failed fetching asset details: ${err.message}` });
        }
      }

      document.getElementById('loading-badge').classList.add('hidden');
      buildDashboard();
      renderCurrentQuestion();
    });

    // 2. Dashboard UI Generator
    function buildDashboard() {
      const container = document.getElementById('dashboard');
      container.innerHTML = '';
      questions.forEach((q, idx) => {
        const btn = document.createElement('button');
        btn.innerText = `Q${idx + 1}`;
        btn.className = `px-4 py-2 text-sm font-semibold rounded-lg border transition-all cursor-pointer ${
          idx === currentIndex 
            ? 'bg-blue-600 border-blue-600 text-white shadow-sm' 
            : 'bg-white border-gray-200 hover:bg-gray-50 text-gray-700'
        }`;
        btn.onclick = () => { currentIndex = idx; renderCurrentQuestion(); };
        container.appendChild(btn);
      });
    }

    // 3. Main State Content Renderer
    function renderCurrentQuestion() {
      buildDashboard();
      const questionArea = document.getElementById('question-area');
      const workingArea = document.getElementById('working-area');
      const answerArea = document.getElementById('answer-area');
      const q = questions[currentIndex];

      if (!q) return;
      if (q.error) {
        questionArea.innerHTML = `<div class="text-red-500 font-medium">⚠️ ${q.message} (${q.id})</div>`;
        workingArea.classList.add('hidden');
        answerArea.classList.add('hidden');
        return;
      }

      let diagramHtml = '';
      if (q.media && q.media.diagram_url) {
        diagramHtml = `
          <div class="mb-6 border border-gray-200 bg-gray-100 rounded-lg w-full h-48 flex items-center justify-center overflow-hidden">
            <img src="${BASE_RAW_URL}${q.media.diagram_url}" alt="Question Diagram" class="object-contain h-full w-full">
          </div>`;
      }

      questionArea.innerHTML = `
        <div class="text-xs font-bold text-blue-600 tracking-wider uppercase mb-1">${q.metadata?.topic || 'General Science'}</div>
        <h2 class="text-xl font-bold text-gray-900 mb-4">Question ID: ${q.id}</h2>
        ${diagramHtml}
        <div id="math-text" class="text-base leading-relaxed text-gray-800 font-normal">${q.question.text}</div>`;

      renderMathInElement(document.getElementById('math-text'), {
        delimiters: [
          { left: "$$", right: "$$", display: true },
          { left: "$", right: "$", display: false }
        ]
      });

      workingArea.classList.remove('hidden');
      document.getElementById('scratchpad').value = localStorage.getItem(`scratchpad-id-${q.id}`) || '';

      answerArea.classList.remove('hidden');
      document.getElementById('answer-input').value = studentAnswers[currentIndex] || '';

      document.getElementById('btn-prev').disabled = (currentIndex === 0);
      if (currentIndex === questions.length - 1) {
        document.getElementById('btn-next').classList.add('hidden');
        document.getElementById('btn-submit').classList.remove('hidden');
      } else {
        document.getElementById('btn-next').classList.remove('hidden');
        document.getElementById('btn-submit').classList.add('hidden');
      }
    }

    function captureAnswer(val) {
      studentAnswers[currentIndex] = val;
    }

    function saveScratchpad() {
      const q = questions[currentIndex];
      if (q && q.id) {
        const val = document.getElementById('scratchpad').value;
        localStorage.setItem(`scratchpad-id-${q.id}`, val);
      }
    }

    function changeQuestion(dir) {
      currentIndex += dir;
      renderCurrentQuestion();
    }

    // 5. Quiz Evaluator Engine - Strictly NO ALERTS
    function submitQuiz() {
      let grandTotalEarned = 0;
      let grandTotalPossible = 0;
      let resultsContainerHtml = "";

      questions.forEach((q, idx) => {
        if (q.error) return;
        
        let questionEarnedMarks = 0;
        let questionMaxMarks = 0;
        
        const studentRawAnswer = studentAnswers[idx] || "";
        const correctRawAnswer = q.solution.final_answer;
        
        // Use a safe fallback if final_answer is missing in YAML
        const targetFinalNum = correctRawAnswer !== undefined ? parseFloat(correctRawAnswer.toString().replace(/[^0-9.-]/g, '')) : NaN;
        const studentFinalNum = parseFloat(studentRawAnswer);

        // Calculate max marks from yaml structure
        const structuredSteps = (q.solution && Array.isArray(q.solution.steps)) ? q.solution.steps : [];
        if (structuredSteps.length > 0) {
          structuredSteps.forEach(s => questionMaxMarks += parseInt(s.marks_assigned || 1));
        } else {
          questionMaxMarks = 1; 
        }

        // Check final answer tolerance
        let finalAnswerCorrect = false;
        if (!isNaN(targetFinalNum) && !isNaN(studentFinalNum)) {
          if (studentFinalNum === targetFinalNum) {
            finalAnswerCorrect = true;
          } else {
            const deviation = Math.abs((studentFinalNum - targetFinalNum) / targetFinalNum);
            if (deviation <= 0.005) finalAnswerCorrect = true;
          }
        }

        let dynamicStepsHtml = "";
        const scratchpadCapturedText = localStorage.getItem(`scratchpad-id-${q.id}`) || "";
        const studentNumbersInWorking = (scratchpadCapturedText.match(/[+-]?\d+(\.\d+)?/g) || []).map(Number);

        if (finalAnswerCorrect) {
          // Rule 1: Correct Final Answer = Full Marks
          questionEarnedMarks = questionMaxMarks;
          if (structuredSteps.length > 0) {
            structuredSteps.forEach(step => {
              dynamicStepsHtml += `
                <div class="flex items-start gap-3 text-sm border-l-2 border-emerald-500 pl-3 py-1 bg-emerald-50/50 rounded-r">
                  <span class="text-emerald-600 font-bold shrink-0">Step ${step.step_number}:</span>
                  <div class="flex-1 text-gray-700">${step.text}</div>
                  <span class="text-xs font-semibold px-2 py-0.5 bg-emerald-100 text-emerald-800 rounded-full shrink-0">Earned: ${step.marks_assigned}/${step.marks_assigned}</span>
                </div>`;
            });
          } else {
            dynamicStepsHtml = `<p class="text-sm text-emerald-600 font-medium">✓ Direct final answer correct. Full marks awarded.</p>`;
          }
        } else {
          // Rule 2: Incorrect Final Answer = Check milestones for partial marks
          if (structuredSteps.length > 0) {
            structuredSteps.forEach((step) => {
              const stepWeight = parseInt(step.marks_assigned || 1);
              let milestoneMatched = false;

              if (step.check_type === "numeric" && step.milestone_value !== undefined) {
                const targetVal = parseFloat(step.milestone_value);
                const tolerancePercent = parseFloat(step.tolerance || 0.005);
                
                for (let num of studentNumbersInWorking) {
                  if (num === targetVal || Math.abs((num - targetVal) / targetVal) <= tolerancePercent) { 
                    milestoneMatched = true; 
                    break; 
                  }
                }
              }

              if (milestoneMatched) {
                questionEarnedMarks += stepWeight;
                dynamicStepsHtml += `
                  <div class="flex items-start gap-3 text-sm border-l-2 border-emerald-500 pl-3 py-1 bg-emerald-50/50 rounded-r">
                    <span class="text-emerald-600 font-bold shrink-0">Step ${step.step_number}:</span>
                    <div class="flex-1 text-gray-700">${step.text}</div>
                    <span class="text-xs font-semibold px-2 py-0.5 bg-emerald-100 text-emerald-800 rounded-full shrink-0">Earned: ${stepWeight}/${stepWeight}</span>
                  </div>`;
              } else {
                dynamicStepsHtml += `
                  <div class="flex items-start gap-3 text-sm border-l-2 border-rose-300 pl-3 py-1 bg-rose-50/30 rounded-r">
                    <span class="text-gray-400 font-bold shrink-0">Step ${step.step_number}:</span>
                    <div class="flex-1 text-gray-500 line-through decoration-gray-300">${step.text}</div>
                    <span class="text-xs font-semibold px-2 py-0.5 bg-gray-100 text-gray-500 rounded-full shrink-0">Earned: 0/${stepWeight}</span>
                  </div>`;
              }
            });
          } else {
            dynamicStepsHtml = `<p class="text-sm text-rose-500 font-medium">✗ Final answer incorrect. No intermediate steps available for partial credit.</p>`;
          }
        }

        grandTotalEarned += questionEarnedMarks;
        grandTotalPossible += questionMaxMarks;

        // Build the HTML card for this question
        resultsContainerHtml += `
          <div class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
            <div class="bg-gray-50 border-b border-gray-200 px-6 py-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
              <div>
                <span class="text-xs font-bold text-blue-600 tracking-wider uppercase">${q.metadata?.topic || 'General Science'}</span>
                <h3 class="text-lg font-bold text-gray-900">Q${idx + 1}: ${q.id}</h3>
              </div>
              <div class="px-4 py-1.5 rounded-full font-mono font-bold text-sm ${questionEarnedMarks === questionMaxMarks ? 'bg-emerald-100 text-emerald-800' : questionEarnedMarks > 0 ? 'bg-amber-100 text-amber-800' : 'bg-rose-100 text-rose-800'}">
                Marks: ${questionEarnedMarks} / ${questionMaxMarks}
              </div>
            </div>

            <div class="p-6 space-y-6">
              <div>
                <h4 class="text-xs font-bold uppercase tracking-wider text-gray-400 mb-1">Question</h4>
                <div class="text-gray-800 text-sm leading-relaxed">${q.question.text}</div>
              </div>

              <div class="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t border-gray-100">
                <div>
                  <h4 class="text-xs font-bold uppercase tracking-wider text-gray-400 mb-1">Your Answer Box</h4>
                  <div class="font-mono text-sm px-3 py-2 border rounded-lg bg-gray-50 inline-block min-w-[12rem] ${finalAnswerCorrect ? 'border-emerald-300 text-emerald-700 bg-emerald-50/20' : 'border-rose-300 text-rose-700 bg-rose-50/20'}">
                    ${studentRawAnswer || '<i>Empty</i>'}
                  </div>
                </div>
                <div>
                  <h4 class="text-xs font-bold uppercase tracking-wider text-gray-400 mb-1">Target Answer</h4>
                  <div class="font-mono text-sm px-3 py-2 border border-blue-200 bg-blue-50/20 text-blue-800 rounded-lg inline-block min-w-[12rem]">
                    ${correctRawAnswer !== undefined ? correctRawAnswer : 'N/A'}
                  </div>
                </div>
              </div>

              <div class="pt-4 border-t border-gray-100">
                <h4 class="text-xs font-bold uppercase tracking-wider text-gray-400 mb-1">Your Working (Read Only)</h4>
                <pre class="w-full bg-slate-50 border border-gray-200 p-3 rounded-lg text-xs font-mono whitespace-pre-wrap text-gray-600 block leading-relaxed">${scratchpadCapturedText || 'No working recorded.'}</pre>
              </div>

              <div class="pt-4 border-t border-gray-100 space-y-2">
                <h4 class="text-xs font-bold uppercase tracking-wider text-gray-400 mb-2">Marking Scheme Breakdown</h4>
                <div class="space-y-2">${dynamicStepsHtml}</div>
              </div>
            </div>
          </div>`;
      });

      // Swap out the interface - HIDE workspace, SHOW results
      document.getElementById('quiz-workspace').classList.add('hidden');
      document.getElementById('dashboard').classList.add('hidden');
      
      const resultsScreen = document.getElementById('quiz-results-screen');
      resultsScreen.classList.remove('hidden');
      
      document.getElementById('results-score-badge').innerText = `${grandTotalEarned} / ${grandTotalPossible}`;
      document.getElementById('results-cards-container').innerHTML = resultsContainerHtml;

      // Re-render Math formatting on the results page
      renderMathInElement(document.getElementById('results-cards-container'), {
        delimiters: [
          { left: "$$", right: "$$", display: true },
          { left: "$", right: "$", display: false }
        ]
      });

      // Scroll to top
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    // 6. Advanced Scientific Calculator Engine
    function pressCalc(token) {
      const display = document.getElementById('calc-display');
      const history = document.getElementById('calc-history');

      if (token === 'AC') {
        calcExpression = "";
        display.innerText = "0";
        history.innerText = "";
      } 
      else if (token === 'DEL') {
        if (calcExpression.length > 0) {
          if (calcExpression.endsWith('sin(') || calcExpression.endsWith('cos(') || calcExpression.endsWith('tan(')) {
            calcExpression = calcExpression.slice(0, -4);
          } else if (calcExpression.endsWith('sqrt(')) {
            calcExpression = calcExpression.slice(0, -5);
          } else if (calcExpression.endsWith('*10^')) {
            calcExpression = calcExpression.slice(0, -4);
          } else if (calcExpression.endsWith('Ans')) {
            calcExpression = calcExpression.slice(0, -3);
          } else {
            calcExpression = calcExpression.slice(0, -1);
          }
        }
        display.innerText = calcExpression || "0";
      } 
      else if (token === '=') {
        try {
          if (calcExpression === "") return;

          const degreeScope = {
            sin: (x) => Math.sin(x * Math.PI / 180),
            cos: (x) => Math.cos(x * Math.PI / 180),
            tan: (x) => Math.tan(x * Math.PI / 180),
            sqrt: (x) => Math.sqrt(x),
            pi: Math.PI,
            Ans: lastAnswer
          };

          let result = math.evaluate(calcExpression, degreeScope);
          
          if (typeof result === 'number') {
            if (result % 1 !== 0) result = parseFloat(result.toFixed(6));
            history.innerText = calcExpression.replace(/\*/g, '×').replace(/\//g, '÷') + " =";
            display.innerText = result;
            lastAnswer = result;
            calcExpression = result.toString();
          }
        } catch (e) {
          display.innerText = "Syntax Error";
          calcExpression = "";
        }
      } 
      else {
        calcExpression += token;
        display.innerText = calcExpression.replace(/\*/g, '×').replace(/\//g, '÷');
      }
    }
  </script>
</body>
</html>
