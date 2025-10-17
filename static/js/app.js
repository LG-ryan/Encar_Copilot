/**
 * Encar Copilot (Endy) - 프론트엔드 JavaScript
 * 사용자 인터페이스 및 API 통신 관리
 */

// 전역 변수
let sessionToken = null;
let currentUser = null;
let allFAQs = []; // 전체 FAQ 목록 캐싱
let questionHistory = []; // 질문 히스토리
let historyIndex = -1; // 히스토리 네비게이션 인덱스
let selectedCategory = 'all'; // 선택된 카테고리

// ==================== 초기화 ====================

document.addEventListener('DOMContentLoaded', () => {
    // 세션 토큰 확인
    const savedToken = localStorage.getItem('sessionToken');
    if (savedToken) {
        // 세션 유효성 검증
        validateSession(savedToken);
    } else {
        showLoginModal();
    }
    
    // FAQ 목록 미리 로드
    loadAllFAQs();
    
    // 자동완성 초기화
    initAutocomplete();
    
    // 공유 버튼 이벤트 리스너 (이벤트 위임)
    document.getElementById('chatMessages').addEventListener('click', (e) => {
        if (e.target.closest('.share-btn')) {
            const btn = e.target.closest('.share-btn');
            const answer = btn.dataset.answer;
            const department = btn.dataset.department;
            const link = btn.dataset.link;
            shareAnswer(answer, department, link);
        }
    });
    
    // 글자 수 카운터 초기화
    initCharCounter();
    
    // 질문 히스토리 초기화
    loadQuestionHistory();
    initHistoryNavigation();
    
    // 검색창 동적 힌트 시작 (약간의 딜레이 후)
    setTimeout(() => {
        startDynamicPlaceholder();
    }, 500);
});

// ==================== 인증 관련 ====================

function showLoginModal() {
    document.getElementById('loginModal').classList.remove('hidden');
}

function hideLoginModal() {
    document.getElementById('loginModal').classList.add('hidden');
}

async function handleLogin(event) {
    event.preventDefault();
    
    const employeeId = document.getElementById('employeeId').value.trim();
    const name = document.getElementById('employeeName').value.trim();
    const errorDiv = document.getElementById('loginError');
    const errorText = document.getElementById('loginErrorText');
    const loginBtn = document.getElementById('loginSubmitBtn');
    const loginText = document.getElementById('loginText');
    const loginSpinner = document.getElementById('loginSpinner');
    
    // 로딩 상태 시작
    loginBtn.disabled = true;
    loginText.textContent = '로그인 중...';
    loginSpinner.classList.remove('hidden');
    errorDiv.classList.add('hidden');
    
    try {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                employee_id: employeeId,
                name: name
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            sessionToken = data.session_token;
            currentUser = data.user;
            
            // 세션 토큰 저장
            localStorage.setItem('sessionToken', sessionToken);
            
            // UI 업데이트
            updateUserInfo();
            hideLoginModal();
            
            // 환영 메시지
            showWelcomeMessage();
            
            // 첫 로그인인지 확인
            const hasSeenGuide = localStorage.getItem('hasSeenGuide');
            if (!hasSeenGuide) {
                // 1초 후 가이드 모달 표시
                setTimeout(() => {
                    showGuideModal();
                    localStorage.setItem('hasSeenGuide', 'true');
                }, 1000);
            }
        } else {
            errorText.textContent = data.message;
            errorDiv.classList.remove('hidden');
        }
    } catch (error) {
        console.error('로그인 오류:', error);
        errorText.textContent = '로그인 중 오류가 발생했습니다.';
        errorDiv.classList.remove('hidden');
    } finally {
        // 로딩 상태 종료
        loginBtn.disabled = false;
        loginText.textContent = '로그인';
        loginSpinner.classList.add('hidden');
    }
}

async function validateSession(token) {
    try {
        const response = await fetch('/api/me', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            sessionToken = token;
            currentUser = data.user;
            updateUserInfo();
            hideLoginModal();
        } else {
            // 세션 무효
            localStorage.removeItem('sessionToken');
            showLoginModal();
        }
    } catch (error) {
        console.error('세션 검증 오류:', error);
        localStorage.removeItem('sessionToken');
        showLoginModal();
    }
}

function updateUserInfo() {
    if (currentUser) {
        document.getElementById('userName').textContent = currentUser.name;
        document.getElementById('teamName').textContent = currentUser.department;
        document.getElementById('userInfo').classList.remove('hidden');
    }
}

async function logout() {
    try {
        await fetch('/api/logout', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${sessionToken}`
            }
        });
    } catch (error) {
        console.error('로그아웃 오류:', error);
    }
    
    // 로컬 데이터 삭제
    sessionToken = null;
    currentUser = null;
    localStorage.removeItem('sessionToken');
    
    // UI 초기화
    document.getElementById('userInfo').classList.add('hidden');
    document.getElementById('chatArea').classList.add('hidden');
    document.getElementById('chatMessages').innerHTML = '';
    
    // 로그인 모달 표시
    showLoginModal();
}

// 채팅창에 웰컴 메시지 추가 (질문 전송 시)
function addWelcomeMessageToChat() {
    console.log('addWelcomeMessageToChat 호출됨');
    const chatMessages = document.getElementById('chatMessages');
    
    // 향상된 웰컴 메시지 with 인기 질문
    const welcomeHtml = `
        <div class="flex justify-start mb-6 fade-in">
            <div class="bg-gradient-to-br from-white to-red-50/30 border border-gray-200 rounded-xl px-6 py-5 max-w-[70%] shadow-md">
                <div class="flex items-center space-x-2 mb-3">
                    <div class="w-8 h-8 bg-gradient-to-br from-red-600 to-red-700 rounded-full flex items-center justify-center shadow-sm">
                        <span class="text-white text-base font-bold">E</span>
                    </div>
                    <span class="text-base font-semibold text-gray-800">엔디(Endy)</span>
                </div>
                
                <div class="text-gray-800 leading-relaxed mb-4">
                    <p class="text-[13px] mb-3">안녕하세요, <strong class="font-semibold text-red-600">${currentUser.name}</strong>님! 👋</p>
                    <p class="text-[13px] text-gray-600">저는 Encar의 든든한 Buddy 엔디예요.<br>HR, IT, 총무, 복리후생 등 궁금한 모든 것을 도와드릴게요!</p>
                </div>
                
                <!-- 인기 질문 섹션 -->
                <div class="mt-4 p-4 bg-white rounded-lg border border-gray-200">
                    <div class="flex items-center gap-2 mb-3">
                        <svg class="w-4 h-4 text-red-600" fill="currentColor" viewBox="0 0 20 20">
                            <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"></path>
                        </svg>
                        <h3 class="text-xs font-bold text-gray-700">많이 묻는 질문</h3>
                    </div>
                    <div class="space-y-2">
                        <button onclick="askSampleQuestion('연차는 언제 생기나요?')" 
                                class="flex items-center gap-2 w-full px-3 py-2 bg-gray-50 hover:bg-red-50 border border-gray-200 hover:border-red-300 rounded-lg text-left transition-all hover:-translate-y-0.5 hover:shadow-sm group">
                            <svg class="w-4 h-4 text-gray-400 group-hover:text-red-600 transition-colors flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"></path>
                            </svg>
                            <span class="text-xs text-gray-700 group-hover:text-gray-900">연차는 언제 생기나요?</span>
                        </button>
                        <button onclick="askSampleQuestion('와이파이 비밀번호가 뭐예요?')" 
                                class="flex items-center gap-2 w-full px-3 py-2 bg-gray-50 hover:bg-red-50 border border-gray-200 hover:border-red-300 rounded-lg text-left transition-all hover:-translate-y-0.5 hover:shadow-sm group">
                            <svg class="w-4 h-4 text-gray-400 group-hover:text-red-600 transition-colors flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path>
                            </svg>
                            <span class="text-xs text-gray-700 group-hover:text-gray-900">와이파이 비밀번호가 뭐예요?</span>
                        </button>
                        <button onclick="askSampleQuestion('휴가는 어떻게 신청하나요?')" 
                                class="flex items-center gap-2 w-full px-3 py-2 bg-gray-50 hover:bg-red-50 border border-gray-200 hover:border-red-300 rounded-lg text-left transition-all hover:-translate-y-0.5 hover:shadow-sm group">
                            <svg class="w-4 h-4 text-gray-400 group-hover:text-red-600 transition-colors flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"></path>
                            </svg>
                            <span class="text-xs text-gray-700 group-hover:text-gray-900">휴가는 어떻게 신청하나요?</span>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    const div = document.createElement('div');
    div.innerHTML = welcomeHtml.trim();
    const welcomeElement = div.firstElementChild;
    
    if (welcomeElement) {
        chatMessages.appendChild(welcomeElement);
        console.log('웰컴 메시지 추가됨');
    } else {
        console.error('웰컴 메시지 생성 실패');
    }
    
    scrollToBottom();
}

// 로그인 시 호출 (기존 함수, welcomeCard만 표시)
function showWelcomeMessage() {
    console.log('showWelcomeMessage 호출됨 (로그인 시)');
    // 로그인 시에는 welcomeCard(흰색 카드)만 표시하고
    // 채팅창은 첫 질문 시에만 웰컴 메시지 표시
}

// ==================== 질문 처리 ====================

async function handleQuestion(event) {
    event.preventDefault();
    
    const input = document.getElementById('questionInput');
    const question = input.value.trim();
    const submitBtn = document.getElementById('submitBtn');
    const submitText = document.getElementById('submitText');
    const submitSpinner = document.getElementById('submitSpinner');
    
    if (!question) return;
    
    // 로딩 상태 시작
    submitBtn.disabled = true;
    input.disabled = true;
    submitText.classList.add('hidden');
    submitSpinner.classList.remove('hidden');
    
    // 입력 필드 초기화
    const savedQuestion = question;
    input.value = '';
    
    // 채팅 영역 표시
    const chatArea = document.getElementById('chatArea');
    const chatMessages = document.getElementById('chatMessages');
    chatArea.classList.remove('hidden');
    
    // 환영 카드 숨기기 (흰색 카드만 숨김)
    const welcomeCard = document.getElementById('welcomeCard');
    if (welcomeCard && !welcomeCard.classList.contains('hidden')) {
        welcomeCard.classList.add('hidden');
        
        // 첫 질문일 때만 웰컴 메시지를 채팅창에 추가
        if (chatMessages.children.length === 0) {
            addWelcomeMessageToChat();
        }
    }
    
    // 질문 히스토리에 저장
    saveQuestionToHistory(savedQuestion);
    
    // 사용자 메시지 추가
    addUserMessage(savedQuestion);
    
    // 로딩 표시
    const loadingId = showLoading();
    
    try {
        const startTime = Date.now();
        
        // ✅ 일반 응답 처리 (스트리밍 비활성화)
        const response = await fetch('/api/ask', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': sessionToken ? `Bearer ${sessionToken}` : ''
            },
            body: JSON.stringify({
                question: savedQuestion,
                user_id: currentUser ? currentUser.employee_id : null
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        const responseTime = ((Date.now() - startTime) / 1000).toFixed(2);
        console.log(`⏱️ 응답 시간: ${responseTime}초`);
        console.log('📦 API 응답 데이터:', data);
        console.log('🔗 유사한 질문:', data.related_questions);
        
        // 로딩 제거
        removeLoading(loadingId);
        
        // 봇 메시지 표시 (유사한 질문, 피드백 버튼 포함)
        addBotMessage(data, responseTime);
        
    } catch (error) {
        console.error('질문 처리 오류:', error);
        removeLoading(loadingId);
        addErrorMessage('죄송해요, 오류가 발생했어요. 다시 시도해주세요.');
    } finally {
        // 로딩 상태 종료
        submitBtn.disabled = false;
        input.disabled = false;
        submitText.classList.remove('hidden');
        submitSpinner.classList.add('hidden');
        
        // 포커스 유지
        input.focus();
    }
}

function askSampleQuestion(question) {
    const input = document.getElementById('questionInput');
    input.value = question;
    
    // 자동으로 폼 제출 (질문 전송)
    const form = input.closest('form');
    if (form) {
        // handleQuestion 함수를 직접 호출
        const event = new Event('submit', { cancelable: true });
        form.dispatchEvent(event);
    }
}

// ==================== 메시지 UI ====================

function addUserMessage(message) {
    const chatMessages = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'flex justify-end mb-3';
    
    // 전역 변수에 마지막 질문 저장
    window.lastUserQuestion = message;
    
    messageDiv.innerHTML = `
        <div class="bg-gray-700 text-white rounded-2xl px-4 py-2.5 max-w-[60%] shadow-sm">
            <p class="text-[13px] leading-relaxed">${escapeHtml(message)}</p>
        </div>
    `;
    
    chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

async function addBotMessage(data, responseTime) {
    const chatMessages = document.getElementById('chatMessages');
    
    // 사용자가 입력한 질문 가져오기
    const userQuestion = window.lastUserQuestion || '';
    
    const messageDiv = createBotMessage(
        data.answer,
        data.department,
        data.link,
        data.related_questions,
        data.category,
        responseTime,
        data.question_id || Date.now(),
        false, // 타이핑 효과 비활성화 (속도 최적화)
        userQuestion // 검색어 전달
    );
    
    chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

function createBotMessage(answer, department, link, relatedQuestions, category, responseTime, questionId, enableTyping = false, userQuestion = '') {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'flex justify-start mb-3';
    
    // Markdown 렌더링 (marked.js 사용)
    marked.setOptions({
        breaks: true,  // 줄바꿈 자동 변환
        gfm: true,     // GitHub Flavored Markdown (표 지원)
    });
    
    let renderedAnswer = marked.parse(answer);
    
    // 키워드 하이라이트/볼드 처리 제거 (Markdown 자체 볼드로 충분)
    // LLM이 이미 중요한 키워드는 **볼드**로 마크다운에 표시하므로 별도 처리 불필요
    
    let html = `
        <div class="bg-gradient-to-br from-white to-red-50/30 border border-gray-200 rounded-xl px-5 py-4 max-w-[60%] shadow-md hover:shadow-lg transition-all duration-300">
            <div class="flex items-center space-x-2 mb-2">
                <div class="w-7 h-7 bg-gradient-to-br from-red-600 to-red-700 rounded-full flex items-center justify-center shadow-sm">
                    <span class="text-white text-sm font-bold">E</span>
                </div>
                <span class="text-sm font-semibold text-gray-800">${escapeHtml(department)}</span>
                ${category ? `<span class="text-xs text-gray-500">·</span><span class="text-xs text-gray-500">${escapeHtml(category)}</span>` : ''}
            </div>
            
            <div class="text-gray-800 text-[13px] leading-relaxed answer-text markdown-content" data-full-answer="${escapeHtml(renderedAnswer)}">${enableTyping ? '' : createCollapsibleAnswer(renderedAnswer)}</div>
    `;
    
    if (link) {
        html += `
            <div class="mt-3">
                <a href="${escapeHtml(link)}" target="_blank" 
                   class="inline-flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 text-white text-sm font-medium rounded-lg shadow-sm hover:shadow-md hover:-translate-y-0.5 active:translate-y-0 transition-all duration-200">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
                    </svg>
                    자세히 보기
                </a>
            </div>
        `;
    }
    
    if (relatedQuestions && relatedQuestions.length > 0) {
        // 답변에 "여러 섹션이 있습니다" 포함 여부로 마인드맵 스타일 판단
        const isMultiSectionMode = answer.includes('여러 섹션이 있습니다');
        
        html += `
            <div class="mt-4 pt-3 border-t border-red-100">
                <div class="mt-4 p-4 bg-white rounded-lg border border-gray-200">
                    <div class="flex items-center gap-2 mb-3">
                        <svg class="w-4 h-4 text-red-600" fill="currentColor" viewBox="0 0 20 20">
                            <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"></path>
                        </svg>
                        <h3 class="text-xs font-bold text-gray-700">${isMultiSectionMode ? '관련 섹션' : '유사한 질문'}</h3>
                    </div>
                    <div class="space-y-2">
        `;
        
        const questionsToShow = Array.isArray(relatedQuestions[0]) ? relatedQuestions : relatedQuestions.slice(0, 3);
        questionsToShow.forEach((q, index) => {
            const questionText = typeof q === 'string' ? q : q.question;
            
            // 엔디 첫 인사말과 완전히 동일한 디자인
            html += `
                <button onclick="askSampleQuestion('${escapeHtml(questionText)}')" 
                        class="flex items-center gap-2 w-full px-3 py-2 bg-gray-50 hover:bg-red-50 border border-gray-200 hover:border-red-300 rounded-lg text-left transition-all hover:-translate-y-0.5 hover:shadow-sm group">
                    <svg class="w-4 h-4 text-gray-400 group-hover:text-red-600 transition-colors flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                    </svg>
                    <span class="text-xs text-gray-700 group-hover:text-gray-900">${escapeHtml(questionText)}</span>
                </button>
            `;
        });
        
        html += `
                    </div>
                </div>
            </div>
        `;
    }
    
    // 피드백 및 공유 버튼 (리플 효과)
    if (questionId) {
        html += `
            <div class="flex items-center gap-2 mt-4 pt-3 border-t border-gray-200">
                <button onclick="submitFeedback(${questionId}, true, '${escapeHtml(userQuestion).replace(/'/g, "\\'")}')" 
                        class="feedback-btn relative overflow-hidden bg-gray-100 hover:bg-green-50 text-gray-600 hover:text-green-600 p-2.5 rounded-lg hover:-translate-y-1 hover:shadow-md active:translate-y-0 transition-all duration-200" 
                        title="도움됨"
                        data-feedback-id="${questionId}-like">
                    <svg class="w-5 h-5 pointer-events-none" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5"></path>
                    </svg>
                </button>
                <button onclick="submitFeedback(${questionId}, false, '${escapeHtml(userQuestion).replace(/'/g, "\\'")}')" 
                        class="feedback-btn relative overflow-hidden bg-gray-100 hover:bg-red-50 text-gray-600 hover:text-red-600 p-2.5 rounded-lg hover:-translate-y-1 hover:shadow-md active:translate-y-0 transition-all duration-200" 
                        title="도움안됨"
                        data-feedback-id="${questionId}-dislike">
                    <svg class="w-5 h-5 pointer-events-none" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14H5.236a2 2 0 01-1.789-2.894l3.5-7A2 2 0 018.736 3h4.018a2 2 0 01.485.06l3.76.94m-7 10v5a2 2 0 002 2h.096c.5 0 .905-.405.905-.904 0-.715.211-1.413.608-2.008L17 13V4m-7 10h2m5-10h2a2 2 0 012 2v6a2 2 0 01-2 2h-2.5"></path>
                    </svg>
                </button>
                <button class="share-btn relative overflow-hidden bg-gray-100 hover:bg-blue-50 text-gray-600 hover:text-blue-600 p-2.5 rounded-lg hover:-translate-y-1 hover:shadow-md active:translate-y-0 transition-all duration-200" 
                        title="공유"
                        data-answer="${escapeHtml(answer)}"
                        data-department="${escapeHtml(department)}"
                        data-link="${escapeHtml(link || '')}">
                    <svg class="w-5 h-5 pointer-events-none" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z"></path>
                    </svg>
                </button>
                <span id="feedback-msg-${questionId}" class="text-xs text-green-600 ml-2 hidden animate-fade-in font-medium">
                    ✓ 의견 주셔서 감사합니다!
                </span>
            </div>
        `;
    }
    
    html += `</div>`;
    
    messageDiv.innerHTML = html;
    return messageDiv;
}

function addErrorMessage(message) {
    const chatMessages = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'flex justify-start fade-in';
    
    messageDiv.innerHTML = `
        <div class="bg-red-100 border border-red-200 rounded-lg px-4 py-3 max-w-[70%]">
            <p class="text-red-800">❌ ${escapeHtml(message)}</p>
        </div>
    `;
    
    chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

function showLoading() {
    const chatMessages = document.getElementById('chatMessages');
    const loadingDiv = document.createElement('div');
    const loadingId = 'loading-' + Date.now();
    loadingDiv.id = loadingId;
    loadingDiv.className = 'flex justify-start fade-in';
    
    // 스켈레톤 UI 로딩
    loadingDiv.innerHTML = `
        <div class="bg-gradient-to-br from-white to-red-50/30 border border-gray-200 rounded-xl px-5 py-4 max-w-[60%] shadow-md">
            <div class="flex items-center space-x-2 mb-3">
                <div class="w-7 h-7 bg-gradient-to-br from-red-600 to-red-700 rounded-full flex items-center justify-center shadow-sm animate-pulse">
                    <span class="text-white text-sm font-bold">E</span>
                </div>
                <div class="h-4 w-24 bg-gray-200 rounded animate-pulse"></div>
            </div>
            
            <!-- 스켈레톤 텍스트 -->
            <div class="space-y-2">
                <div class="h-3 w-full bg-gray-200 rounded animate-pulse"></div>
                <div class="h-3 w-5/6 bg-gray-200 rounded animate-pulse" style="animation-delay: 0.1s"></div>
                <div class="h-3 w-4/6 bg-gray-200 rounded animate-pulse" style="animation-delay: 0.2s"></div>
            </div>
            
            <div class="flex items-center gap-2 mt-3 pt-2">
                <svg class="w-4 h-4 text-red-600 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span class="text-xs text-gray-500">엔디가 답을 찾고 있어요...</span>
            </div>
        </div>
    `;
    
    chatMessages.appendChild(loadingDiv);
    scrollToBottom();
    
    return loadingId;
}

function removeLoading(loadingId) {
    const loadingDiv = document.getElementById(loadingId);
    if (loadingDiv) {
        loadingDiv.remove();
    }
}

function scrollToBottom() {
    const chatMessages = document.getElementById('chatMessages');
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// ==================== 피드백 ====================

async function submitFeedback(questionId, isHelpful, userQuestion) {
    console.log('submitFeedback 호출:', questionId, isHelpful);
    
    const likeBtn = document.querySelector(`[data-feedback-id="${questionId}-like"]`);
    const dislikeBtn = document.querySelector(`[data-feedback-id="${questionId}-dislike"]`);
    
    // 이미 선택된 버튼을 다시 클릭하면 취소
    const currentBtn = isHelpful ? likeBtn : dislikeBtn;
    const isAlreadySelected = currentBtn.classList.contains('bg-green-100') || currentBtn.classList.contains('bg-red-100');
    
    if (isAlreadySelected) {
        // 피드백 취소
        showToast('✅ 피드백이 취소되었습니다');
        resetFeedbackButtons(questionId);
        return;
    }
    
    try {
        // 즉시 Toast 메시지 표시
        showToast(isHelpful ? '✅ 도움이 되었다니 기쁩니다!' : '📝 소중한 의견 감사합니다!');
        
        // 피드백 메시지 표시
        const feedbackMsg = document.getElementById(`feedback-msg-${questionId}`);
        if (feedbackMsg) {
            feedbackMsg.classList.remove('hidden');
            feedbackMsg.textContent = '✓ 의견 주셔서 감사합니다!';
        }
        
        // 이전 선택 초기화
        resetFeedbackButtons(questionId);
        
        // 클릭된 버튼만 강조
        if (isHelpful) {
            likeBtn.classList.add('ring-2', 'ring-green-500', 'text-green-600', 'bg-green-100');
            likeBtn.classList.remove('text-gray-600');
        } else {
            dislikeBtn.classList.add('ring-2', 'ring-red-500', 'text-red-600', 'bg-red-100');
            dislikeBtn.classList.remove('text-gray-600');
        }
        
        const response = await fetch('/api/feedback', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': sessionToken ? `Bearer ${sessionToken}` : ''
            },
            body: JSON.stringify({
                question_id: questionId,
                user_question: userQuestion,
                is_helpful: isHelpful,
                user_id: currentUser ? currentUser.employee_id : null
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // 3초 후 메시지 페이드아웃
            setTimeout(() => {
                if (feedbackMsg) {
                    feedbackMsg.classList.add('opacity-0', 'transition-opacity', 'duration-500');
                }
            }, 3000);
            
            // 부정 피드백인 경우 상세 의견 수집
            if (!isHelpful) {
                setTimeout(() => {
                    showDetailedFeedbackForm(questionId, userQuestion);
                }, 500);
            }
        }
    } catch (error) {
        console.error('피드백 제출 오류:', error);
        showToast('❌ 피드백 전송 실패. 다시 시도해주세요.');
    }
}

function resetFeedbackButtons(questionId) {
    const buttons = document.querySelectorAll(`[data-feedback-id^="${questionId}"]`);
    buttons.forEach(btn => {
        btn.classList.remove(
            'ring-2', 'ring-green-500', 'ring-red-500',
            'text-green-600', 'text-red-600',
            'bg-green-100', 'bg-red-100',
            'opacity-75', 'cursor-not-allowed'
        );
        btn.classList.add('text-gray-600');
        btn.disabled = false;
    });
}

function showDetailedFeedbackForm(questionId, userQuestion) {
    const chatMessages = document.getElementById('chatMessages');
    const feedbackDiv = document.createElement('div');
    feedbackDiv.className = 'flex justify-start fade-in';
    feedbackDiv.id = `detailed-feedback-${questionId}`;
    
    feedbackDiv.innerHTML = `
        <div class="bg-yellow-50 border border-yellow-200 rounded-lg px-4 py-3 max-w-[70%]">
            <p class="text-sm font-medium text-gray-800 mb-3">😢 아쉬워요. 어떤 점이 부족했나요?</p>
            
            <div class="space-y-2 mb-3">
                <label class="flex items-center text-sm text-gray-700 hover:bg-yellow-100 p-2 rounded cursor-pointer transition">
                    <input type="checkbox" value="wrong_answer" class="feedback-reason mr-2">
                    <span>답변이 정확하지 않아요</span>
                </label>
                <label class="flex items-center text-sm text-gray-700 hover:bg-yellow-100 p-2 rounded cursor-pointer transition">
                    <input type="checkbox" value="not_helpful" class="feedback-reason mr-2">
                    <span>도움이 되지 않아요</span>
                </label>
                <label class="flex items-center text-sm text-gray-700 hover:bg-yellow-100 p-2 rounded cursor-pointer transition">
                    <input type="checkbox" value="incomplete" class="feedback-reason mr-2">
                    <span>정보가 부족해요</span>
                </label>
                <label class="flex items-center text-sm text-gray-700 hover:bg-yellow-100 p-2 rounded cursor-pointer transition">
                    <input type="checkbox" value="outdated" class="feedback-reason mr-2">
                    <span>정보가 오래되었어요</span>
                </label>
            </div>
            
            <textarea 
                id="feedbackComment-${questionId}"
                class="w-full p-2 border border-gray-300 rounded text-sm resize-none focus:outline-none focus:ring-2 focus:ring-yellow-500"
                placeholder="자세한 의견을 남겨주세요 (선택사항)"
                rows="2"></textarea>
            
            <div class="flex space-x-2 mt-3">
                <button onclick="submitDetailedFeedback(${questionId}, '${escapeHtml(userQuestion).replace(/'/g, "\\'")}')"
                        class="flex-1 px-3 py-2 bg-red-600 text-white rounded text-sm font-medium hover:bg-red-700 transition">
                    의견 보내기
                </button>
                <button onclick="cancelDetailedFeedback(${questionId})"
                        class="px-3 py-2 bg-gray-200 text-gray-700 rounded text-sm hover:bg-gray-300 transition">
                    취소
                </button>
            </div>
        </div>
    `;
    
    chatMessages.appendChild(feedbackDiv);
    scrollToBottom();
}

async function submitDetailedFeedback(questionId, userQuestion) {
    const feedbackDiv = document.getElementById(`detailed-feedback-${questionId}`);
    const checkboxes = feedbackDiv.querySelectorAll('.feedback-reason:checked');
    const comment = document.getElementById(`feedbackComment-${questionId}`).value;
    
    const reasons = Array.from(checkboxes).map(cb => cb.value);
    
    // 상세 피드백 데이터
    const detailedFeedback = {
        question_id: questionId,
        user_question: userQuestion,
        is_helpful: false,
        reasons: reasons,
        comment: comment || null,
        user_id: currentUser ? currentUser.employee_id : null,
        matched_section: null  // 나중에 답변 데이터에서 가져올 수 있음
    };
    
    try {
        // 상세 피드백 API 호출
        const response = await fetch('/api/feedback/detailed', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': sessionToken || ''
            },
            body: JSON.stringify(detailedFeedback)
        });
        
        if (!response.ok) {
            throw new Error('상세 피드백 전송 실패');
        }
        
        const result = await response.json();
        console.log('✅ 상세 피드백 저장 성공:', result);
        
        // 피드백 폼 제거
        feedbackDiv.remove();
        
        // 감사 메시지
        showToast('소중한 의견 감사합니다! 개선에 참고하겠습니다. 🙏');
        
    } catch (error) {
        console.error('❌ 상세 피드백 제출 오류:', error);
        showToast('피드백 전송에 실패했습니다. 다시 시도해주세요.');
    }
}

function cancelDetailedFeedback(questionId) {
    const feedbackDiv = document.getElementById(`detailed-feedback-${questionId}`);
    if (feedbackDiv) {
        feedbackDiv.remove();
    }
}

function showToast(message) {
    const toast = document.createElement('div');
    toast.className = 'fixed bottom-4 right-4 bg-gray-800 text-white px-4 py-2 rounded-lg shadow-lg z-50 fade-in';
    toast.textContent = message;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, 3000);
}

// ==================== 유틸리티 ====================

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 타이핑 효과 (마크다운 지원)
function typeWriter(element, text, speed = 5) {
    return new Promise((resolve) => {
        // 공백 최소화된 텍스트 변환
        const cleanText = text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/^#{1,6}\s+/gm, '')
            .replace(/\n\n+/g, '\n')  // 연속된 줄바꿈을 하나로
            .replace(/\n/g, '<br>');
        const renderedHTML = cleanText;
        
        // HTML에서 순수 텍스트 추출
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = renderedHTML;
        const plainText = tempDiv.textContent || tempDiv.innerText;
        
        let i = 0;
        element.textContent = '';
        
        function type() {
            if (i < plainText.length) {
                element.textContent += plainText.charAt(i);
                i++;
                scrollToBottom();
                setTimeout(type, speed);
            } else {
                // 타이핑 완료 후 마크다운 렌더링 HTML 적용
                element.innerHTML = renderedHTML;
                scrollToBottom();
                resolve();
            }
        }
        
        type();
    });
}

// ==================== 자동완성 ====================

async function loadAllFAQs() {
    try {
        const response = await fetch('/api/questions');
        const data = await response.json();
        if (data.success) {
            allFAQs = data.questions;
        }
    } catch (error) {
        console.error('FAQ 로드 오류:', error);
    }
}

function initAutocomplete() {
    const input = document.getElementById('questionInput');
    const autocompleteList = document.getElementById('autocompleteList');
    let currentFocus = -1;
    
    // 디바운스 함수
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            clearTimeout(timeout);
            timeout = setTimeout(() => func(...args), wait);
        };
    }
    
    // 자동완성 검색
    const searchAutocomplete = debounce(async (query) => {
        if (query.length < 2) {
            autocompleteList.classList.add('hidden');
            return;
        }
        
        // 매칭되는 질문 찾기 (카테고리 필터 적용)
        const matches = allFAQs.filter(faq => {
            const questionLower = faq.question.toLowerCase();
            const queryLower = query.toLowerCase();
            const matchesQuery = questionLower.includes(queryLower);
            const matchesCategory = selectedCategory === 'all' || faq.category === selectedCategory;
            return matchesQuery && matchesCategory;
        }).slice(0, 5); // 최대 5개
        
        if (matches.length === 0) {
            autocompleteList.classList.add('hidden');
            return;
        }
        
        // 자동완성 목록 생성
        autocompleteList.innerHTML = matches.map((faq, index) => `
            <div class="autocomplete-item px-4 py-3 hover:bg-gray-50 cursor-pointer border-b last:border-b-0 transition"
                 data-index="${index}"
                 data-question="${escapeHtml(faq.question)}">
                <div class="flex items-center justify-between">
                    <div class="flex-1">
                        <span class="text-sm text-gray-800">${highlightMatch(faq.question, query)}</span>
                        <span class="text-xs text-gray-500 ml-2">· ${escapeHtml(faq.category)}</span>
                    </div>
                    <svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7l5 5m0 0l-5 5m5-5H6"></path>
                    </svg>
                </div>
            </div>
        `).join('');
        
        autocompleteList.classList.remove('hidden');
        
        // 클릭 이벤트 추가
        document.querySelectorAll('.autocomplete-item').forEach(item => {
            item.addEventListener('click', () => {
                input.value = item.getAttribute('data-question');
                autocompleteList.classList.add('hidden');
                input.focus();
            });
        });
    }, 300);
    
    // 입력 이벤트
    input.addEventListener('input', (e) => {
        searchAutocomplete(e.target.value);
        currentFocus = -1;
    });
    
    // 키보드 네비게이션
    input.addEventListener('keydown', (e) => {
        const items = document.querySelectorAll('.autocomplete-item');
        
        if (e.key === 'ArrowDown') {
            e.preventDefault();
            currentFocus++;
            addActive(items);
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            currentFocus--;
            addActive(items);
        } else if (e.key === 'Enter') {
            if (currentFocus > -1 && items[currentFocus]) {
                e.preventDefault();
                items[currentFocus].click();
            }
        } else if (e.key === 'Escape') {
            autocompleteList.classList.add('hidden');
        }
    });
    
    function addActive(items) {
        if (!items || items.length === 0) return;
        
        // 모든 항목에서 active 제거
        items.forEach(item => item.classList.remove('bg-gray-100'));
        
        // 범위 조정
        if (currentFocus >= items.length) currentFocus = 0;
        if (currentFocus < 0) currentFocus = items.length - 1;
        
        // active 추가
        items[currentFocus].classList.add('bg-gray-100');
        items[currentFocus].scrollIntoView({ block: 'nearest' });
    }
    
    // 외부 클릭 시 닫기
    document.addEventListener('click', (e) => {
        if (!input.contains(e.target) && !autocompleteList.contains(e.target)) {
            autocompleteList.classList.add('hidden');
        }
    });
}

function highlightMatch(text, query) {
    const regex = new RegExp(`(${query})`, 'gi');
    return escapeHtml(text).replace(regex, '<mark class="bg-yellow-200 font-medium">$1</mark>');
}

// ==================== 글자 수 카운터 ====================

function initCharCounter() {
    const input = document.getElementById('questionInput');
    const charCount = document.getElementById('charCount');
    
    input.addEventListener('input', () => {
        const length = input.value.length;
        charCount.textContent = length;
        
        // 180자 이상이면 경고 색상
        if (length >= 180) {
            charCount.classList.add('text-red-600', 'font-medium');
        } else {
            charCount.classList.remove('text-red-600', 'font-medium');
        }
    });
}

// ==================== 질문 히스토리 ====================

function loadQuestionHistory() {
    const saved = localStorage.getItem('questionHistory');
    if (saved) {
        questionHistory = JSON.parse(saved);
    }
}

function saveQuestionToHistory(question) {
    // 중복 제거
    questionHistory = questionHistory.filter(q => q !== question);
    
    // 최신 질문을 맨 앞에 추가
    questionHistory.unshift(question);
    
    // 최대 10개만 저장
    questionHistory = questionHistory.slice(0, 10);
    
    // LocalStorage에 저장
    localStorage.setItem('questionHistory', JSON.stringify(questionHistory));
    
    // 히스토리 인덱스 리셋
    historyIndex = -1;
}

function showQuestionHistorySection() {
    if (questionHistory.length === 0) return;
    
    const welcomeCard = document.getElementById('welcomeCard');
    if (!welcomeCard || welcomeCard.classList.contains('hidden')) return;
    
    // 기존 히스토리 섹션 제거
    const existingHistory = document.getElementById('questionHistorySection');
    if (existingHistory) {
        existingHistory.remove();
    }
    
    const historySection = document.createElement('div');
    historySection.id = 'questionHistorySection';
    historySection.className = 'mt-4 pt-4 border-t border-gray-200';
    
    historySection.innerHTML = `
        <div class="flex items-center justify-between mb-2">
            <h3 class="text-sm font-medium text-gray-700 flex items-center">
                📜 최근 질문
                <span class="ml-2 text-xs text-gray-500">(${questionHistory.length}개)</span>
            </h3>
            <button onclick="clearQuestionHistory()" 
                    class="text-xs text-gray-500 hover:text-red-600 transition">
                전체 삭제
            </button>
        </div>
        <div class="space-y-1">
            ${questionHistory.slice(0, 5).map(q => `
                <button onclick="askSampleQuestion('${escapeHtml(q).replace(/'/g, "\\'")} ')" 
                        class="block w-full text-left px-3 py-2 bg-gray-50 hover:bg-gray-100 rounded-lg text-sm text-gray-700 transition flex items-center justify-between group">
                    <span class="flex-1 truncate">${escapeHtml(q)}</span>
                    <svg class="w-4 h-4 text-gray-400 opacity-0 group-hover:opacity-100 transition" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7l5 5m0 0l-5 5m5-5H6"></path>
                    </svg>
                </button>
            `).join('')}
        </div>
    `;
    
    welcomeCard.appendChild(historySection);
}

function clearQuestionHistory() {
    if (confirm('모든 질문 히스토리를 삭제하시겠습니까?')) {
        questionHistory = [];
        localStorage.removeItem('questionHistory');
        
        const historySection = document.getElementById('questionHistorySection');
        if (historySection) {
            historySection.remove();
        }
        
        showToast('질문 히스토리가 삭제되었습니다');
    }
}

function initHistoryNavigation() {
    const input = document.getElementById('questionInput');
    
    input.addEventListener('keydown', (e) => {
        // 화살표 위: 이전 질문
        if (e.key === 'ArrowUp' && e.ctrlKey) {
            e.preventDefault();
            if (questionHistory.length === 0) return;
            
            if (historyIndex < questionHistory.length - 1) {
                historyIndex++;
                input.value = questionHistory[historyIndex];
            }
        }
        // 화살표 아래: 다음 질문
        else if (e.key === 'ArrowDown' && e.ctrlKey) {
            e.preventDefault();
            
            if (historyIndex > 0) {
                historyIndex--;
                input.value = questionHistory[historyIndex];
            } else if (historyIndex === 0) {
                historyIndex = -1;
                input.value = '';
            }
        }
    });
}

// ==================== 카테고리 필터 ====================

async function filterCategory(category) {
    console.log('[filterCategory] 호출됨:', category);
    selectedCategory = category;
    
    // 모든 버튼 스타일 리셋
    document.querySelectorAll('.category-filter').forEach(btn => {
        btn.classList.remove('bg-red-600', 'text-white', 'font-medium');
        btn.classList.add('bg-gray-100', 'text-gray-700');
    });
    
    // 선택된 버튼 하이라이트
    const selectedBtn = document.querySelector(`[data-category="${category}"]`);
    if (selectedBtn) {
        selectedBtn.classList.remove('bg-gray-100', 'text-gray-700');
        selectedBtn.classList.add('bg-red-600', 'text-white', 'font-medium');
    }
    
    // 정보 텍스트 업데이트
    const infoText = document.getElementById('categoryFilterInfo');
    if (infoText) {
        if (category === 'all') {
            infoText.textContent = '💡 전체 카테고리에서 검색합니다';
        } else {
            infoText.textContent = `💡 ${category} 카테고리에서만 검색합니다`;
        }
    }
    
    // 예시 질문 필터링
    filterExampleQuestions(category);
    
    // 카테고리 클릭 시 대표 질문 표시 (전체 제외)
    if (category !== 'all') {
        console.log('[filterCategory] showCategoryQuestions 호출 예정:', category);
        await showCategoryQuestions(category);
    }
}

/**
 * 카테고리별 대표 질문 표시
 */
async function showCategoryQuestions(category) {
    console.log('[showCategoryQuestions] 시작:', category);
    try {
        const url = `/api/category/${encodeURIComponent(category)}/questions`;
        console.log('[showCategoryQuestions] 요청 URL:', url);
        console.log('[showCategoryQuestions] sessionToken:', sessionToken ? '있음' : '없음');
        
        const response = await fetch(url, {
            headers: {
                'Authorization': sessionToken ? `Bearer ${sessionToken}` : ''
            }
        });
        
        console.log('[showCategoryQuestions] 응답 상태:', response.status);
        
        const data = await response.json();
        console.log('[showCategoryQuestions] 응답 데이터:', data);
        
        if (!data.success || !data.questions || data.questions.length === 0) {
            console.log('[showCategoryQuestions] 질문 없음 또는 실패');
            return;
        }
        
        // 대화방에 카테고리 질문 메시지 추가
        console.log('[showCategoryQuestions] 질문 메시지 추가:', data.questions.length, '개');
        addCategoryQuestionsMessage(category, data.questions);
        
    } catch (error) {
        console.error('[showCategoryQuestions] 오류:', error);
    }
}

/**
 * 카테고리 대표 질문 메시지 생성 (엔디 인사말 '많이 묻는 질문'과 동일한 디자인)
 */
function addCategoryQuestionsMessage(category, questions) {
    const chatMessages = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'flex justify-start mb-3';
    
    // 카테고리별 아이콘 (사람 아이콘으로 통일)
    const categoryIcons = {
        'HR': '👤',
        'IT': '💻',
        '총무': '📋',
        '복리후생': '🎁',
        '비즈니스': '💼',
        '기업 소개': '🏢'
    };
    
    const categoryIcon = categoryIcons[category] || '📌';
    
    let html = `
        <div class="bg-gradient-to-br from-white to-red-50/30 border border-gray-200 rounded-xl px-5 py-4 max-w-[60%] shadow-md hover:shadow-lg transition-all duration-300">
            <div class="flex items-center space-x-2 mb-2">
                <div class="w-7 h-7 bg-gradient-to-br from-red-600 to-red-700 rounded-full flex items-center justify-center shadow-sm">
                    <span class="text-white text-sm font-bold">E</span>
                </div>
                <span class="text-sm font-semibold text-gray-800">엔디(Endy)</span>
                <span class="text-xs text-gray-500">·</span>
                <span class="text-xs text-gray-500">${category}</span>
            </div>
            
            <div class="mt-4 p-4 bg-white rounded-lg border border-gray-200">
                <div class="flex items-center gap-2 mb-3">
                    <svg class="w-4 h-4 text-red-600" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"></path>
                    </svg>
                    <h3 class="text-xs font-bold text-gray-700">${categoryIcon} ${category} 자주 묻는 질문</h3>
                </div>
                <div class="space-y-2">
    `;
    
    // 질문 버튼 생성 (최대 10개, 엔디 인사말과 동일한 스타일)
    questions.slice(0, 10).forEach((question, index) => {
        html += `
            <button onclick="askSampleQuestion('${escapeHtml(question)}')" 
                    class="flex items-center gap-2 w-full px-3 py-2 bg-gray-50 hover:bg-red-50 border border-gray-200 hover:border-red-300 rounded-lg text-left transition-all hover:-translate-y-0.5 hover:shadow-sm group">
                <svg class="w-4 h-4 text-gray-400 group-hover:text-red-600 transition-colors flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
                <span class="text-xs text-gray-700 group-hover:text-gray-900">${escapeHtml(question)}</span>
            </button>
        `;
    });
    
    html += `
                </div>
            </div>
        </div>
    `;
    
    messageDiv.innerHTML = html;
    chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

function filterExampleQuestions(category) {
    const exampleButtons = document.querySelectorAll('.example-question-btn');
    
    exampleButtons.forEach(btn => {
        const btnCategory = btn.getAttribute('data-category');
        
        if (category === 'all' || btnCategory === category) {
            btn.style.display = 'block';
        } else {
            btn.style.display = 'none';
        }
    });
}

// ==================== 답변 공유 ====================

async function shareAnswer(answer, department, link) {
    // Markdown을 일반 텍스트로 변환 (간단한 변환)
    const plainTextAnswer = answer
        .replace(/\*\*(.*?)\*\*/g, '$1')  // 볼드 제거
        .replace(/\*(.*?)\*/g, '$1')  // 이탤릭 제거
        .replace(/#{1,6}\s+/g, '')  // 헤더 제거
        .replace(/\|/g, ' ')  // 표 구분자 제거
        .trim();
    
    const shareText = `📌 엔디(Endy)의 답변\n\n${plainTextAnswer}\n\n담당: ${department}${link ? `\n\n📄 상세 문서: ${link}` : ''}\n\n✨ Encar Copilot: ${window.location.href}`;
    
    // 즉시 시각적 피드백
    showToast('📋 클립보드에 복사 중...');
    
    // Web Share API 지원 확인
    if (navigator.share) {
        try {
            await navigator.share({
                title: '엔디(Endy)의 답변',
                text: shareText,
                url: window.location.href
            });
            showToast('✅ 답변이 공유되었습니다!');
        } catch (error) {
            if (error.name !== 'AbortError') {
                // 공유 실패 시 클립보드로 폴백
                copyToClipboard(shareText);
            }
        }
    } else {
        // Web Share API 미지원 시 클립보드 복사
        copyToClipboard(shareText);
    }
}

function copyToClipboard(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(() => {
            showToast('✅ 클립보드에 복사되었습니다!');
        }).catch(() => {
            // Fallback: 텍스트 영역 사용
            fallbackCopyToClipboard(text);
        });
    } else {
        fallbackCopyToClipboard(text);
    }
}

function fallbackCopyToClipboard(text) {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.left = '-9999px';
    document.body.appendChild(textArea);
    textArea.select();
    
    try {
        document.execCommand('copy');
        showToast('✅ 클립보드에 복사되었습니다!');
    } catch (err) {
        showToast('❌ 복사 실패. 다시 시도해주세요.');
    }
    
    document.body.removeChild(textArea);
}

// ==================== 유틸리티 함수 ====================

/**
 * 사용자 질문에서 키워드 추출
 */
function extractKeywords(question) {
    // 불용어 목록 (검색에 불필요한 단어)
    const stopWords = ['은', '는', '이', '가', '을', '를', '에', '에서', '의', '와', '과', '로', '으로', 
                       '어떻게', '어디', '무엇', '뭐', '어떤', '어느', '있나요', '있어요', '하나요', '해요', 
                       '인가요', '입니까', '합니까', '나요', '까요', '?', '!', '.'];
    
    // 문장을 단어로 분리 (한글, 영문, 숫자만)
    const words = question.match(/[가-힣a-zA-Z0-9]+/g) || [];
    
    // 불용어 제거 및 2글자 이상 필터링
    const keywords = words.filter(word => 
        word.length >= 2 && !stopWords.includes(word)
    );
    
    // 중복 제거
    return [...new Set(keywords)];
}

/**
 * 긴 답변에 더보기/접기 토글 추가
 */
function createCollapsibleAnswer(html) {
    // <br> 개수로 길이 판단 (약 10줄 이상)
    const lineCount = (html.match(/<br>/g) || []).length;
    const charCount = html.replace(/<[^>]*>/g, '').length; // 태그 제외한 순수 텍스트 길이
    
    // 10줄 이상 또는 500자 이상이면 접기
    if (lineCount >= 10 || charCount >= 500) {
        // 첫 5줄 또는 200자까지만 미리보기로 표시
        let preview = html;
        const brMatches = html.match(/(<br>)/g);
        
        if (brMatches && brMatches.length >= 5) {
            const fifthBrIndex = html.split('<br>', 6).slice(0, 5).join('<br>').length;
            preview = html.substring(0, fifthBrIndex + 4); // +4 for '<br>'
        } else if (charCount >= 300) {
            preview = html.substring(0, 300);
        }
        
        const uniqueId = 'collapse-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
        
        return `
            <div id="${uniqueId}-preview" class="collapsible-preview">
                ${preview}
                ${lineCount >= 5 ? '<br>...' : '...'}
            </div>
            <div id="${uniqueId}-full" class="collapsible-full hidden">
                ${html}
            </div>
            <button 
                onclick="toggleCollapse('${uniqueId}')" 
                class="mt-2 text-red-600 hover:text-red-700 font-medium text-xs flex items-center gap-1 transition-colors"
                id="${uniqueId}-btn"
            >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
                </svg>
                <span>더보기</span>
            </button>
        `;
    }
    
    return html;
}

/**
 * 답변 접기/펼치기 토글
 */
function toggleCollapse(id) {
    const preview = document.getElementById(id + '-preview');
    const full = document.getElementById(id + '-full');
    const btn = document.getElementById(id + '-btn');
    
    if (preview && full && btn) {
        const isExpanded = full.classList.contains('hidden');
        
        if (isExpanded) {
            // 펼치기
            preview.classList.add('hidden');
            full.classList.remove('hidden');
            btn.innerHTML = `
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7"></path>
                </svg>
                <span>접기</span>
            `;
        } else {
            // 접기
            preview.classList.remove('hidden');
            full.classList.add('hidden');
            btn.innerHTML = `
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
                </svg>
                <span>더보기</span>
            `;
        }
    }
}

// 전역 스코프에 함수 등록
window.toggleCollapse = toggleCollapse;
window.showGuideModal = showGuideModal;
window.hideGuideModal = hideGuideModal;
window.filterCategory = filterCategory;

// ==================== 가이드 모달 ====================

function showGuideModal() {
    document.getElementById('guideModal').classList.remove('hidden');
}

function hideGuideModal() {
    document.getElementById('guideModal').classList.add('hidden');
}

// ==================== 검색창 동적 힌트 ====================

/**
 * 검색창 플레이스홀더를 동적으로 변경하여 질문 예시 제공
 */
function startDynamicPlaceholder() {
    const input = document.getElementById('questionInput');
    if (!input) return;
    
    const hints = [
        '연차는 언제 쓸 수 있어?',
        '급여명세서 어디서 확인해?',
        '출장비 신청 방법은?',
        '휴가 신청은 어떻게 해?',
        '경조사 지원은 뭐가 있어?',
        '근무시간은 몇 시부터야?',
        '사내 복리후생 알려줘',
        '그룹웨어 로그인 어떻게 해?',
        'VPN 설정 방법 알려줘',
        '비교견적 서비스가 뭐야?'
    ];
    
    let currentIndex = 0;
    const defaultPlaceholder = '엔디(Endy)에게 물어보기...';
    
    // 3초마다 힌트 변경
    setInterval(() => {
        // 입력 중이거나 포커스 되어 있으면 변경하지 않음
        if (input.value.trim() !== '' || document.activeElement === input) {
            return;
        }
        
        currentIndex = (currentIndex + 1) % hints.length;
        input.placeholder = hints[currentIndex];
        
        // 5초 후 기본 플레이스홀더로 복원
        setTimeout(() => {
            if (input.value.trim() === '' && document.activeElement !== input) {
                input.placeholder = defaultPlaceholder;
            }
        }, 2500);
    }, 5000);
    
    // 포커스 시 기본 플레이스홀더로 복원
    input.addEventListener('focus', () => {
        input.placeholder = defaultPlaceholder;
    });
}

/**
 * 마크다운 테이블을 HTML 테이블로 변환
 */
/**
 * [태그] 형식을 대형 배지와 스타일링된 박스로 변환
 */
function renderSectionIcons(html) {
    // 미니멀 인라인 배지로 변경 (작은 회색 배지, 한 줄 띄우기)
    const badges = {
        '[요약]': '<br><span class="inline-block px-2 py-1 bg-gray-200 text-gray-700 text-xs font-medium rounded mr-1">요약</span> ',
        '[상세]': '<br><span class="inline-block px-2 py-1 bg-gray-200 text-gray-700 text-xs font-medium rounded mr-1">상세</span> ',
        '[참고]': '<br><span class="inline-block px-2 py-1 bg-gray-200 text-gray-700 text-xs font-medium rounded mr-1">참고</span> ',
        '[주의사항]': '<br><span class="inline-block px-2 py-1 bg-gray-200 text-gray-700 text-xs font-medium rounded mr-1">주의사항</span> '
    };
    
    // 각 태그를 인라인 배지로 교체
    for (const [tag, badgeHtml] of Object.entries(badges)) {
        const regex = new RegExp(tag.replace(/[[\]]/g, '\\$&'), 'g');
        html = html.replace(regex, badgeHtml);
    }
    
    return html;
}

function convertMarkdownTables(text) {
    // <br> 태그를 임시로 줄바꿈으로 복원
    let content = text.replace(/<br>/g, '\n');
    
    // 개선된 마크다운 테이블 패턴 (더 유연하게)
    const tableRegex = /\|(.+?)\|[\r\n]+\|[-:\s|]+\|[\r\n]+((?:\|.+?\|[\r\n]*)+)/g;
    
    content = content.replace(tableRegex, (match, headerRow, bodyRows) => {
        // 헤더 파싱
        const headers = headerRow.split('|').map(h => h.trim()).filter(h => h);
        
        // 본문 파싱
        const rows = bodyRows.trim().split('\n').filter(r => r.trim() && r.includes('|'));
        
        if (headers.length === 0 || rows.length === 0) return match;
        
        // HTML 테이블 생성
        let html = '<div class="my-4 overflow-x-auto rounded-lg border border-gray-300 shadow-sm">';
        html += '<table class="min-w-full border-collapse text-sm">';
        
        // 헤더
        html += '<thead class="bg-gradient-to-r from-red-50 to-orange-50"><tr>';
        headers.forEach(header => {
            html += `<th class="border border-gray-300 px-4 py-2.5 text-left font-semibold text-gray-800">${header}</th>`;
        });
        html += '</tr></thead>';
        
        // 본문
        html += '<tbody class="bg-white">';
        rows.forEach((row, idx) => {
            const cells = row.split('|').map(c => c.trim()).filter(c => c);
            if (cells.length > 0) {
                const bgClass = idx % 2 === 0 ? 'bg-white' : 'bg-gray-50';
                html += `<tr class="${bgClass} hover:bg-blue-50 transition-colors">`;
                cells.forEach(cell => {
                    html += `<td class="border border-gray-300 px-4 py-2.5 text-gray-700">${cell}</td>`;
                });
                html += '</tr>';
            }
        });
        html += '</tbody></table></div>';
        
        return html;
    });
    
    // 줄바꿈을 다시 <br>로 변환
    return content.replace(/\n/g, '<br>');
}

// ==================== 키보드 단축키 ====================

document.addEventListener('keydown', (event) => {
    // ESC 키로 로그인 모달 닫기 방지
    if (event.key === 'Escape' && !sessionToken) {
        event.preventDefault();
    }
});

