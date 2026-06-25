const messagesEl = document.getElementById('messages');
const chatInput = document.getElementById('chatInput');
const sendButton = document.getElementById('sendButton');
const cameraModal = document.getElementById('cameraModal');
const cameraVideo = document.getElementById('cameraVideo');
const cameraPreview = document.getElementById('cameraPreview');
const cameraModalTitle = document.getElementById('cameraModalTitle');
const photoInput = document.getElementById('photoInput');
const homeContent = document.getElementById('homeContent');
const chatPanel = document.getElementById('chatPanel');
const sidebar = document.getElementById('sidebar');
const sidebarOverlay = document.getElementById('sidebarOverlay');
const glassesBtn = document.getElementById('glassesBtn');
const newChatBtn = document.getElementById('newChatBtn');

// Onboarding and Auth Element References
const onboardingOverlay = document.getElementById('onboardingOverlay');
const introView = document.getElementById('introView');
const authView = document.getElementById('authView');
const introStartBtn = document.getElementById('introStartBtn');
const tabLogin = document.getElementById('tabLogin');
const tabSignup = document.getElementById('tabSignup');
const authUsernameInput = document.getElementById('authUsername');
const authPasswordInput = document.getElementById('authPassword');
const confirmPasswordWrapper = document.getElementById('confirmPasswordWrapper');
const authConfirmInput = document.getElementById('authConfirmPassword');
const authSubmitBtn = document.getElementById('authSubmitBtn');
// Profile and Settings Element References
const sidebarProfileBtn = document.getElementById('sidebarProfileBtn');
const sidebarAvatar = document.getElementById('sidebarAvatar');
const sidebarUsernameDisplay = document.getElementById('sidebarUsernameDisplay');
const settingsModal = document.getElementById('settingsModal');
const settingsAvatar = document.getElementById('settingsAvatar');
const settingsUsernameDisplay = document.getElementById('settingsUsernameDisplay');
// Device Pairing Elements
const deviceOverlay = document.getElementById('deviceOverlay');
const settingsAddGlassesBtn = document.getElementById('settingsAddGlassesBtn');
const startPairingBtn = document.getElementById('startPairingBtn');
const dashboardOverlay = document.getElementById('dashboardOverlay');
const stopButton = document.getElementById('stopButton');
let currentAbortController = null;
let currentPendingMessageEl = null;
// Device State Tracking
let isDeviceConnected = false;
let heartbeatInterval = null;
// Global Tracking State
let currentAuthMode = 'login'; // Can be 'login' or 'signup'
let currentUsername = localStorage.getItem('username') || null;
let currentChatId = null; // Tracks which thread we are currently inside
let activeAction = null;
let sessionId = sessionStorage.getItem('sessionId');
if (!sessionId) {
    sessionId = generateSessionId();
    sessionStorage.setItem('sessionId', sessionId);
}
let cameraStream = null;
let chatMode = false;
let activeChip = null;
let failedPings = 0;
let isPolling = false;
let lastHardwareStatus = "IDLE"; // Track previous state to prevent double-captures
let isFetchingImage = false; 
let lastHistoryLength = 0;
let lastHardwareChatId = null; // Track the most recent chat created strictly by hardware

// 1. Transition from Splash text to Login/Signup card
introStartBtn.addEventListener('click', () => {
    introView.classList.add('hidden'); // Hide the intro layout
    authView.classList.remove('hidden'); // Reveal the login layout
});

// 2. Switch tab to "Log In"
tabLogin.addEventListener('click', () => {
    currentAuthMode = 'login';
    tabLogin.classList.add('active');
    tabSignup.classList.remove('active');
    confirmPasswordWrapper.classList.add('hidden'); // Hide confirm field
    authSubmitBtn.textContent = 'Log In';
});

// 3. Switch tab to "Sign Up"
tabSignup.addEventListener('click', () => {
    currentAuthMode = 'signup';
    tabSignup.classList.add('active');
    tabLogin.classList.remove('active');
    confirmPasswordWrapper.classList.remove('hidden'); // Show confirm field
    authSubmitBtn.textContent = 'Create Account';
});

// 4. Form submission handler
authSubmitBtn.addEventListener('click', () => {
    const usernameVal = authUsernameInput.value.trim();
    const passwordVal = authPasswordInput.value;
    const confirmVal = authConfirmInput.value;

    // Simple structural validation
    if (!usernameVal || !passwordVal) {
        showCustomModal('Missing Fields', 'Please fill out all fields.', 'alert');
        return;
    }

    if (currentAuthMode === 'signup' && passwordVal !== confirmVal) {
        showCustomModal('Password Mismatch', 'Passwords do not match.', 'alert');
        return;
    }

    // Success: Commit the user record to the device's storage
    localStorage.setItem('username', usernameVal);
    currentUsername = usernameVal;
    updateProfileDisplays();

    // Fade out and remove the onboarding layer completely
    onboardingOverlay.style.opacity = '0';
    setTimeout(() => {
        onboardingOverlay.classList.add('hidden');
    }, 400);

    console.log(`User logged in successfully as: ${currentUsername}`);
});

window.onload = function () {
    if (currentUsername) {
        // User already exists! Completely bypass the onboarding overlays
        onboardingOverlay.classList.add('hidden');
        updateProfileDisplays(); // Update UI avatars immediately
        console.log(`Welcome back, ${currentUsername}`);
        loadHistory();
    } else {
        // New user or cleared cache: ensure overlay is standing visible
        onboardingOverlay.classList.remove('hidden');
    }
};

async function loadHistory() {
    if (!currentUsername) return;

    try {
        const res = await fetch(`/get_sessions?username=${encodeURIComponent(currentUsername)}`);
        const sessions = await res.json();
        const historyList = document.getElementById('historyList');

        if (sessions && sessions.length > 0) {
            historyList.innerHTML = '<div style="font-size:0.8rem; color:var(--muted); margin-bottom: 8px;">Recent Chats</div>';

            sessions.forEach(session => {
                const btn = document.createElement('button');
                btn.className = 'history-item';
                btn.style.cssText = "display:block; width:100%; text-align:left; padding:10px 14px; background:var(--surface2); border:none; border-radius:10px; font-size:0.85rem; color:var(--text); margin-bottom:8px; cursor:pointer; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;";
                btn.textContent = session.title;

                // When you click a past chat, load it!
                btn.onclick = () => loadSpecificChat(session.id);
                historyList.appendChild(btn);
            });
        } else {
            historyList.innerHTML = '<div class="sidebar-placeholder">No recent chats</div>';
        }
    } catch (err) {
        console.error("Could not load sessions:", err);
    }
}

async function loadSpecificChat(chatId) {
    currentChatId = chatId; // Lock onto this specific thread
    closeSidebar();
    enterChatMode();
    messagesEl.innerHTML = ''; // Clear the screen

    try {
        const res = await fetch(`/get_chat?username=${encodeURIComponent(currentUsername)}&chat_id=${chatId}`);
        const history = await res.json();
        lastHistoryLength = history.length;

        history.forEach(item => {
            if (item.type && item.type.startsWith('image_') && item.image_file) {
                let label = item.type === 'image_ocr' ? 'Text Recognition' : 'Object Identification';
                addImageMessage(`/get_image?username=${encodeURIComponent(currentUsername)}&filename=${item.image_file}`, label);
                if (item.bot) addBotMessage(item.bot);
            } else {
                if (item.user) addUserMessage(item.user);
                if (item.bot) addBotMessage(item.bot);
            }
        });
    } catch (err) {
        console.error("Could not load chat:", err);
    }
}

function cancelProcessing() {
    if (currentAbortController) {
        currentAbortController.abort(); // Triggers the AbortError in our fetch blocks
    }
}

function startNewChat() {
    goHome();
}

function addSidebarItem(text) {
    const historyList = document.getElementById('historyList');
    const placeholder = historyList.querySelector('.sidebar-placeholder');
    if (placeholder) placeholder.remove();

    const div = document.createElement('div');
    div.style.padding = '10px 14px';
    div.style.background = 'var(--surface2)';
    div.style.borderRadius = '10px';
    div.style.fontSize = '0.85rem';
    div.style.color = 'var(--text)';
    div.style.marginBottom = '8px';
    div.style.whiteSpace = 'nowrap';
    div.style.overflow = 'hidden';
    div.style.textOverflow = 'ellipsis';
    div.textContent = text;
    historyList.append(div);
}

// Dynamically updates the avatars and text with the user's name
function updateProfileDisplays() {
    if (currentUsername) {
        // Get the first letter and make it uppercase
        const initial = currentUsername.charAt(0).toUpperCase();

        // Update the Pinned Sidebar Profile
        sidebarAvatar.textContent = initial;
        sidebarUsernameDisplay.textContent = currentUsername;

        // Update the Settings Modal Profile
        settingsAvatar.textContent = initial;
        settingsUsernameDisplay.textContent = currentUsername;
    }
}

// 1. Open the Settings Modal when clicking the sidebar profile
sidebarProfileBtn.addEventListener('click', () => {
    // A. Close the sidebar using the correct CSS class
    sidebar.classList.remove('active');
    sidebarOverlay.classList.remove('active');

    // B. Open the settings modal using the CSS .active system (opacity + pointer-events)
    settingsModal.classList.add('active');
});

// 2. Close the Settings Modal
function closeSettingsModal() {
    settingsModal.classList.remove('active');
}

// ==========================================================================
// READLENS GLASSES PAIRING FLOW (META AI INSPIRED)
// ==========================================================================

// 1. Function to open the Device Overlay
// ==========================================================================
// READLENS GLASSES CONNECTION & DASHBOARD FLOW
// ==========================================================================

// 1. Unified function to handle button clicks based on current state
function handleGlassesButtonClick() {
    // Cleanly close settings if we clicked from there
    if (settingsModal && settingsModal.classList.contains('active')) {
        closeSettingsModal();
    }

    if (isDeviceConnected) {
        // We are connected! Open the Dashboard, NOT the pairing screen.
        dashboardOverlay.classList.remove('hidden');
        dashboardOverlay.style.opacity = '1';
    } else {
        // Not connected. Open the Pairing Overlay.
        if (startPairingBtn) {
            startPairingBtn.textContent = 'Add Device';
            startPairingBtn.classList.remove('btn-searching');
            startPairingBtn.style.backgroundColor = '';
            startPairingBtn.style.color = '';
        }
        deviceOverlay.classList.remove('hidden');
        deviceOverlay.style.opacity = '1';
    }
}

// Attach opening logic to BOTH entry point buttons
if (settingsAddGlassesBtn) settingsAddGlassesBtn.addEventListener('click', handleGlassesButtonClick);
if (glassesBtn) glassesBtn.addEventListener('click', handleGlassesButtonClick);

// Overlay Closers
function closeDeviceOverlay() {
    deviceOverlay.style.opacity = '0';
    setTimeout(() => deviceOverlay.classList.add('hidden'), 300);
}

function closeDashboardOverlay() {
    dashboardOverlay.style.opacity = '0';
    setTimeout(() => dashboardOverlay.classList.add('hidden'), 300);
}

if (startPairingBtn) {
    startPairingBtn.addEventListener('click', async () => {
        if (startPairingBtn.classList.contains('btn-searching')) return;

        startPairingBtn.innerHTML = 'Searching for ESP32... <span class="hourglass-spin">⏳</span>';
        startPairingBtn.classList.add('btn-searching');

        try {
            // Call the backend to use the subnet auto-discovery
            const response = await fetch('/connect_device', { method: 'POST' });
            const data = await response.json();

            // If the ESP32 replies with our success message
            if (response.ok && data.status === "connected") {
                startPairingBtn.innerHTML = '✅ Device Paired!';
                startPairingBtn.style.backgroundColor = '#10b981';
                startPairingBtn.style.color = '#ffffff';

                isDeviceConnected = true;
                updateGlassesButtonsUI();
                startHeartbeat(); // Start checking if it's still alive

                setTimeout(() => {
                    closeDeviceOverlay();
                }, 1500);
            } else {
                showCustomModal('Connection Error', 'Handshake rejected by device.', 'alert');
                resetPairingButton();
            }
        } catch (error) {
            console.error(error);
            showCustomModal('Connection Error', 'Could not find your readlens. Ensure it is powered on.', 'alert');
            resetPairingButton();
        }
    });
}

function resetPairingButton() {
    startPairingBtn.innerHTML = 'Add Device';
    startPairingBtn.classList.remove('btn-searching');
}

// 3. UI Update Function (Turns buttons green and blinking)
function updateGlassesButtonsUI() {
    const connectedHTML = '<span class="blink-dot">●</span> Connected';
    const disconnectedHTML = `
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="12" y1="2" x2="12" y2="8"></line><line x1="9" y1="5" x2="15" y2="5"></line><circle cx="6" cy="16" r="4"></circle><circle cx="18" cy="16" r="4"></circle><path d="M10 16a2 2 0 0 0 4 0"></path><path d="M2.5 14L5 8"></path><path d="M21.5 14L19 8"></path>
        </svg> Glasses`;

    if (isDeviceConnected) {
        if (glassesBtn) {
            glassesBtn.classList.add('btn-is-connected');
            glassesBtn.innerHTML = connectedHTML;
            glassesBtn.classList.remove('hidden');
        }
        if (settingsAddGlassesBtn) {
            settingsAddGlassesBtn.classList.add('btn-is-connected');
            settingsAddGlassesBtn.innerHTML = connectedHTML;
        }
    } else {
        if (glassesBtn) {
            glassesBtn.classList.remove('btn-is-connected');
            glassesBtn.innerHTML = disconnectedHTML;
            if (chatMode) {
                glassesBtn.classList.add('hidden');
            } else {
                glassesBtn.classList.remove('hidden');
            }
        }
        if (settingsAddGlassesBtn) {
            settingsAddGlassesBtn.classList.remove('btn-is-connected');
            settingsAddGlassesBtn.innerHTML = '<span>👓</span> Pair readlens Glasses';
        }
    }
}

// --- Loading Overlay Controller Functions ---
function showHardwareLoading(mode) {
    const overlay = document.getElementById('hardwareLoading');
    const textEl = document.getElementById('hardwareLoadingText');
    if (!overlay || !textEl) return;

    // Dynamically adjust messaging based on hardware toggle state
    if (mode === 'ocr') {
        textEl.textContent = '🔍 readlens: Scanning text matrix...';
    } else if (mode === 'object_detection') {
        textEl.textContent = '👁️ readlens: Analyzing target object...';
    } else {
        textEl.textContent = '⚡ readlens: Streaming snapshot...';
    }
    overlay.classList.add('active');
}

function hideHardwareLoading() {
    const overlay = document.getElementById('hardwareLoading');
    if (overlay) overlay.classList.remove('active');
}

// --- High-Speed Heartbeat Engine Loop ---
function startHeartbeat() {
    if (heartbeatInterval) clearTimeout(heartbeatInterval);
    failedPings = 0;
    isPolling = true;

    console.log("Glasses tracking routine active via Backend Ping");

    async function poll() {
        if (!isPolling) return;
        
        try {
            const res = await fetch(`/ping_device?username=${encodeURIComponent(currentUsername)}`);
            const data = await res.json();
            
            if (!res.ok || data.status !== "alive") throw new Error("Offline");
            
            failedPings = 0; 
            
            // Toggle Hardware Loading Screen based on backend state
            if (data.hardware_status && data.hardware_status.startsWith('PROCESSING_')) {
                if (lastHardwareStatus !== data.hardware_status) {
                    const mode = data.hardware_status === 'PROCESSING_OCR' ? 'ocr' : 'object_detection';
                    showHardwareLoading(mode);
                }
            } else if (data.hardware_status === 'IDLE' && lastHardwareStatus && lastHardwareStatus.startsWith('PROCESSING_')) {
                hideHardwareLoading();
            }
            lastHardwareStatus = data.hardware_status || 'IDLE';

            // Check if hardware forced a new chat creation (only jump if it's a NEW hardware chat)
            if (data.latest_hardware_chat_id && data.latest_hardware_chat_id !== lastHardwareChatId) {
                lastHardwareChatId = data.latest_hardware_chat_id;
                // Instantly jump to the newly created chat
                loadSpecificChat(data.latest_hardware_chat_id);
                loadHistory(); // Refresh the sidebar
                // After a forced jump, skip the auto-refresh branch below this tick —
                // we just loaded that chat and don't need to fetch it again.
            }
            // Otherwise, auto-refresh the current chat to show hardware captures.
            // Suppressed when the current chat IS the newest hardware chat (we just
            // jumped to it) — else the post-jump poll sees a length delta and
            // re-fetches the same chat for no reason.
            else if (chatMode && currentChatId && currentChatId !== lastHardwareChatId) {
                try {
                    const chatRes = await fetch(`/get_chat?username=${encodeURIComponent(currentUsername)}&chat_id=${currentChatId}`);
                    const history = await chatRes.json();
                    if (history.length > lastHistoryLength) {
                        loadSpecificChat(currentChatId);
                    }
                } catch (e) {
                    console.error("Failed to auto-refresh chat", e);
                }
            }
            
        } catch (err) {
            failedPings++;
            console.warn(`Ping failed count: ${failedPings}`);
            if (failedPings >= 5) {
                console.warn("Hardware heartbeat lost. Safe disconnect triggered.");
                disconnectDevice(true); 
                return;
            }
        }
        
        if (isPolling) {
            heartbeatInterval = setTimeout(poll, 1500); // 1.5s for fast loading response
        }
    }
    
    poll();
}

function disconnectDevice(isAuto = false) {
    isDeviceConnected = false;
    isPolling = false;
    if (heartbeatInterval) clearTimeout(heartbeatInterval);
    updateGlassesButtonsUI();
    closeDashboardOverlay();

    if (isAuto) {
        // Optional: show a small alert if the device walked out of range
        console.warn("Connection lost. Device walked out of range or powered off.");
    }
}

// 3. The Secure Logout Sequence
function triggerLogout() {
    showCustomModal('Log Out', 'Are you sure you want to log out?', 'confirm', (confirmed) => {
        if (confirmed) {
            // Erase memory from phone
            localStorage.removeItem('username');
            currentUsername = null;

            // Hide settings and sidebar
            closeSettingsModal();
            sidebar.classList.remove('active');
            sidebarOverlay.classList.remove('active');

            // Bring the dark onboarding overlay back up
            onboardingOverlay.style.opacity = '1';
            onboardingOverlay.classList.remove('hidden');

            // Reset the login form text boxes
            authUsernameInput.value = '';
            authPasswordInput.value = '';
            tabLogin.click(); // Switch back to login tab by default

            // Clear chat screen (optional, but good for privacy)
            messagesEl.innerHTML = '';

            console.log("User logged out securely.");
        }
    });
}

// --- CUSTOM MODAL SYSTEM ---
function showCustomModal(title, message, type = 'alert', confirmCallback = null) {
    const overlay = document.getElementById('customModalOverlay');
    const titleEl = document.getElementById('customModalTitle');
    const msgEl = document.getElementById('customModalMessage');
    const cancelBtn = document.getElementById('customModalCancelBtn');
    const confirmBtn = document.getElementById('customModalConfirmBtn');

    titleEl.textContent = title;
    msgEl.textContent = message;

    // Reset button events
    confirmBtn.onclick = null;
    cancelBtn.onclick = null;

    if (type === 'confirm') {
        cancelBtn.style.display = 'block';
        confirmBtn.textContent = 'Log Out';
        
        cancelBtn.onclick = () => {
            closeCustomModal();
            if (confirmCallback) confirmCallback(false);
        };
        confirmBtn.onclick = () => {
            closeCustomModal();
            if (confirmCallback) confirmCallback(true);
        };
    } else {
        cancelBtn.style.display = 'none';
        confirmBtn.textContent = 'OK';
        
        confirmBtn.onclick = () => {
            closeCustomModal();
            if (confirmCallback) confirmCallback(true);
        };
    }

    overlay.classList.remove('hidden');
    overlay.style.opacity = '1';
}

function closeCustomModal() {
    const overlay = document.getElementById('customModalOverlay');
    overlay.style.opacity = '0';
    setTimeout(() => {
        overlay.classList.add('hidden');
    }, 300);
}

function goHome() {
    chatMode = false;
    currentChatId = null; // Drop current thread
    messagesEl.innerHTML = '<div class="message bot">Welcome to readlens. Choose an action above or type a message below.</div>';
    chatPanel.classList.remove('active');
    homeContent.classList.remove('hidden');
    if (glassesBtn) glassesBtn.classList.remove('hidden');
    if (newChatBtn) newChatBtn.classList.add('hidden');
    closeSidebar();
}

photoInput.addEventListener('change', handlePhotoUpload);
document.getElementById('hamburgerBtn').addEventListener('click', openSidebar);

function generateSessionId() {
    return 'sess_' + Math.random().toString(36).substr(2, 9) + Date.now().toString(36);
}

// Sidebar
function openSidebar() { sidebar.classList.add('active'); sidebarOverlay.classList.add('active'); }
function closeSidebar() { sidebar.classList.remove('active'); sidebarOverlay.classList.remove('active'); }

// Chip toggle
function toggleChipOptions(action) {
    const floatId = action === 'ocr' ? 'floatOcr' : 'floatObj';
    const otherId = action === 'ocr' ? 'floatObj' : 'floatOcr';
    document.getElementById(otherId).classList.remove('active');

    const el = document.getElementById(floatId);
    if (el.classList.contains('active')) {
        el.classList.remove('active');
        activeAction = null;
    } else {
        el.classList.add('active');
        activeAction = action;
    }
}

// Close chips when clicking outside
document.addEventListener('click', (e) => {
    if (!e.target.closest('.chip')) {
        document.querySelectorAll('.float-options').forEach(f => f.classList.remove('active'));
    }
});

function triggerInput(type) {
    document.querySelectorAll('.float-options').forEach(f => f.classList.remove('active'));
    if (type === 'camera') openCamera();
    else photoInput.click();
}

function handlePhotoUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => processImage(reader.result);
    reader.readAsDataURL(file);
    photoInput.value = '';
}

// Chat mode
function enterChatMode() {
    if (chatMode) return;
    chatMode = true;
    homeContent.classList.add('hidden');
    chatPanel.classList.add('active');
    if (glassesBtn && !isDeviceConnected) glassesBtn.classList.add('hidden');
    if (newChatBtn) newChatBtn.classList.remove('hidden');
}

function handleInput(el) {
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 120) + 'px';
    const hasText = el.value.trim().length > 0;
    // CSS .send-btn starts at opacity:0 / scale(0.8); the .visible class
    // flips it to opacity:1 / scale(1). Toggling the class is what actually
    // reveals the button — do NOT set inline opacity, it would desync the
    // transform animation.
    if (hasText) {
        sendButton.classList.add('visible');
    } else {
        sendButton.classList.remove('visible');
    }
}

function handleEnter(event) {
    if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); sendChat(); }
}

// Camera
async function openCamera() {
    cameraModalTitle.textContent = activeAction === 'ocr' ? 'Capture Text' : 'Capture Objects';
    cameraModal.classList.add('active');
    cameraPreview.classList.add('hidden');
    cameraVideo.classList.remove('hidden');
    try {
        cameraStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } });
        cameraVideo.srcObject = cameraStream;
    } catch (err) {
        addBotMessage('Unable to access camera. Check permissions.');
        closeCameraModal();
    }
}

function closeCameraModal() {
    cameraModal.classList.remove('active');
    if (cameraStream) { cameraStream.getTracks().forEach(t => t.stop()); cameraStream = null; }
}

function capturePhoto() {
    if (!cameraStream) return;
    // Guard: on some devices the video track hasn't produced its first frame
    // yet, so videoWidth/height are 0. Drawing a 0x0 canvas yields a 1x1
    // JPEG that the server can't analyse — fail fast instead of uploading it.
    const w = cameraVideo.videoWidth;
    const h = cameraVideo.videoHeight;
    if (!w || !h) {
        addBotMessage('Camera is still initialising — try again in a moment.');
        closeCameraModal();
        return;
    }
    const canvas = document.createElement('canvas');
    canvas.width = w;
    canvas.height = h;
    canvas.getContext('2d').drawImage(cameraVideo, 0, 0, canvas.width, canvas.height);
    const imageData = canvas.toDataURL('image/jpeg', 0.9);
    closeCameraModal();
    processImage(imageData);
}

async function processImage(imageData) {
    enterChatMode();
    // Show the image preview in the chat as a user message
    addImageMessage(imageData, activeAction === 'ocr' ? 'Text Recognition' : 'Object Identification');
    
    currentPendingMessageEl = addBotMessage('Processing image...');
    currentAbortController = new AbortController();

    // Toggle Buttons (Hide Send, Show Stop). Clear inline display instead
    // of forcing 'block' — the stylesheet defines .send-btn as grid, and
    // resetting to '' falls back to that rule so the circular shape survives.
    if (stopButton) stopButton.style.display = 'block';
    if (sendButton) sendButton.style.display = 'none';

    try {
        const res = await fetch('/process_image', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                action: activeAction,
                image_source: imageData,
                username: currentUsername,
                chat_id: currentChatId
            }),
            signal: currentAbortController.signal // Attach the abort signal
        });
        const data = await res.json();
        currentChatId = data.chat_id;
        
        removePendingMessage(currentPendingMessageEl);
        addBotMessage(data.text);
    } catch (err) {
        removePendingMessage(currentPendingMessageEl);
        if (err.name === 'AbortError') {
            const cancelMsg = addBotMessage('[Processing cancelled by user]');
            cancelMsg.style.fontStyle = 'italic';
            cancelMsg.style.color = 'var(--muted)';
        } else {
            addBotMessage('Image processing failed. Please try again.');
        }
    } finally {
        // Reset Buttons
        if (stopButton) stopButton.style.display = 'none';
        if (sendButton) sendButton.style.display = '';
        currentAbortController = null;
    }
}

async function sendChat() {
    const text = chatInput.value.trim();
    if (!text) return;
    enterChatMode();
    addUserMessage(text);
    // Don't add a sidebar row for every message typed — sidebar entries are
    // owned by loadHistory / loadSpecificChat, which populate from the
    // server's sessions list. (Only the first message of a brand-new chat
    // would warrant an entry, and that path goes through loadHistory()
    // after the fetch resolves.)
    chatInput.value = '';
    handleInput(chatInput);
    
    currentPendingMessageEl = addBotMessage('Thinking...');
    currentAbortController = new AbortController();

    // Toggle Buttons (Hide Mic, Show Stop)
    if (stopButton) stopButton.style.display = 'block';
    if (sendButton) sendButton.style.display = 'none';

    try {
        const res = await fetch('/chatbot', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: text,
                username: currentUsername,
                chat_id: currentChatId
            }),
            signal: currentAbortController.signal // Attach the abort signal
        });
        const data = await res.json();
        currentChatId = data.chat_id;

        removePendingMessage(currentPendingMessageEl);
        addBotMessage(data.text);
        loadHistory();
    } catch (err) {
        removePendingMessage(currentPendingMessageEl);
        if (err.name === 'AbortError') {
            const cancelMsg = addBotMessage('[Processing cancelled by user]');
            cancelMsg.style.fontStyle = 'italic';
            cancelMsg.style.color = 'var(--muted)';
        } else {
            addBotMessage('Chat failed. Please try again.');
        }
    } finally {
        // Reset Buttons
        if (stopButton) stopButton.style.display = 'none';
        if (sendButton) sendButton.style.display = '';
        currentAbortController = null;
    }
}

function addUserMessage(text) {
    const msg = document.createElement('div');
    msg.className = 'message user'; msg.textContent = text;
    messagesEl.appendChild(msg); messagesEl.scrollTop = messagesEl.scrollHeight;
    return msg;
}

function addImageMessage(imageData, label) {
    const wrapper = document.createElement('div');
    wrapper.className = 'message user image-message';

    const badge = document.createElement('div');
    badge.className = 'image-badge';
    badge.textContent = label;

    const img = document.createElement('img');
    img.src = imageData;
    img.alt = label;
    img.className = 'chat-image-preview';

    wrapper.appendChild(badge);
    wrapper.appendChild(img);
    messagesEl.appendChild(wrapper);
    messagesEl.scrollTop = messagesEl.scrollHeight;
    return wrapper;
}

function addBotMessage(text) {
    const msg = document.createElement('div');
    msg.className = 'message bot'; msg.textContent = text;
    messagesEl.appendChild(msg); messagesEl.scrollTop = messagesEl.scrollHeight;
    return msg;
}
function removePendingMessage(el) { if (el?.parentNode) el.parentNode.removeChild(el); }

// ── Intro logo: mouse parallax tilt (desktop only, after entry) ──
(function () {
    const logo = document.getElementById('introLogo');
    if (!logo) return;

    // Only activate after the snap-in finishes (~1.6s)
    setTimeout(() => {
        document.addEventListener('mousemove', (e) => {
            const cx = window.innerWidth  / 2;
            const cy = window.innerHeight / 2;
            const dx = (e.clientX - cx) / cx; // -1 → 1
            const dy = (e.clientY - cy) / cy;
            // Blend with idle by overriding via inline style only on mouse presence
            logo.style.transform = `
                translateZ(0px)
                rotateY(${dx * 10}deg)
                rotateX(${-dy * 8}deg)
                scale(1)
            `;
        });

        document.addEventListener('mouseleave', () => {
            // Return control to idle CSS animation
            logo.style.transform = '';
        });
    }, 1650);
})();
