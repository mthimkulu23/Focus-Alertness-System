document.addEventListener('DOMContentLoaded', (event) => {
    // --- UI Elements ---
    const videoFeedElement = document.getElementById('videoFeed');
    const faceCountElement = document.getElementById('faceCount');
    const sleepingStatusElement = document.getElementById('sleepingStatus');
    const focusScoreElement = document.getElementById('focusScore');
    const unauthorizedActivityElement = document.getElementById('unauthorizedActivity');
    const copyAttemptElement = document.getElementById('copyAttempt');
    const proctoringAlertElement = document.getElementById('proctoringAlert');
    const alertSound = document.getElementById('alertSound'); // Audio element for beep

    // --- Analytics and Alert Configuration ---
    const ANALYTICS_REFRESH_INTERVAL = 1000; // Refresh analytics every 1 second (1000 ms)
    
    // For debouncing alerts (preventing rapid, annoying repetitions)
    const lastAlertTimestamp = new Map(); // Stores last played timestamp for each alert type
    const alertDebounceTime = 5000; // 5 seconds debounce for the same alert type

    // Map alert types to specific messages for Text-to-Speech
    const alertMessages = {
        "copy_attempt": "Warning! Multiple persons detected. Possible copying.",
        "gaze_violation": "Warning! Unwanted movement detected. Please face the screen.",
        "absent_violation": "Alert! Person not detected. Please return to the screen.",
        "drowsiness": "Attention! Drowsiness detected. Please stay alert.",
        "yawn": "Yawn detected. Please maintain focus.",
        "system_violation": "Security Alert! Tab switched or external application detected."
    };

    let currentSpeakingUtterance = null; // To keep track of the current speech

    // --- Audio and Speech Functions ---
    function playAlertSound() {
        if (alertSound) {
            alertSound.currentTime = 0; // Reset sound to start
            alertSound.play().catch(e => console.error("Error playing sound:", e));
        }
    }

    function speakAlert(message) {
        if ('speechSynthesis' in window) {
            const utterance = new SpeechSynthesisUtterance(message);
            utterance.rate = 1.0; // Normal speech rate
            utterance.pitch = 1.0; // Normal pitch

            // Find a suitable voice (optional, for better voice quality)
            const voices = window.speechSynthesis.getVoices();
            const preferredVoice = voices.find(voice => voice.name.includes('Google US English')) ||
                                   voices.find(voice => voice.lang === 'en-US' && voice.name.includes('female')) ||
                                   voices.find(voice => voice.lang.startsWith('en'));
            if (preferredVoice) {
                utterance.voice = preferredVoice;
            }

            // Cancel previous speech to avoid overlapping, and store current utterance
            window.speechSynthesis.cancel();
            currentSpeakingUtterance = utterance; // Store reference to current utterance
            window.speechSynthesis.speak(utterance);

            utterance.onend = () => {
                currentSpeakingUtterance = null; // Clear reference when speech ends
            };
            utterance.onerror = (e) => {
                console.error("SpeechSynthesisUtterance error:", e);
                currentSpeakingUtterance = null;
            };

        } else {
            console.warn("Text-to-Speech not supported in this browser.");
        }
    }

    // Function to stop all ongoing alerts (sound and speech)
    function stopAllAlerts() {
        if (alertSound && !alertSound.paused) {
            alertSound.pause();
            alertSound.currentTime = 0; // Rewind for next play
            console.log("Alert sound stopped.");
        }
        if ('speechSynthesis' in window && window.speechSynthesis.speaking) {
            window.speechSynthesis.cancel();
            currentSpeakingUtterance = null;
            console.log("SpeechSynthesis stopped.");
        }
    }

    // --- Main Function to Fetch and Update Analytics ---
    async function fetchAnalytics() {
        try {
            const response = await fetch('/analytics'); // Using relative path for Flask endpoint
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();

            // --- Update UI Elements ---
            faceCountElement.textContent = data.face_count;
            sleepingStatusElement.textContent = data.sleeping_status;
            focusScoreElement.textContent = data.focus_score.toFixed(2); // Format to 2 decimal places
            unauthorizedActivityElement.textContent = data.unauthorized_activity;
            copyAttemptElement.textContent = data.copy_attempt;
            proctoringAlertElement.textContent = data.proctoring_alert;

            // --- Update Status Text Colors and Alert Styling ---
            // Sleeping Status
            if (data.sleeping_status.includes("Sleeping")) {
                sleepingStatusElement.className = 'text-red-600 text-lg font-bold';
            } else if (data.sleeping_status.includes("No person")) {
                 sleepingStatusElement.className = 'text-gray-500 text-lg font-bold';
            } else if (data.sleeping_status.includes("Yawning")) {
                 sleepingStatusElement.className = 'text-orange-600 text-lg font-bold'; // Indicate yawning differently
            }
            else {
                sleepingStatusElement.className = 'text-green-600 text-lg font-bold';
            }

            // Unauthorized Activity
            if (data.unauthorized_activity === "None Detected" || data.unauthorized_activity === "No Person Detected") {
                unauthorizedActivityElement.className = 'text-gray-500 text-lg font-bold';
            } else {
                unauthorizedActivityElement.className = 'text-red-600 text-lg font-bold';
            }

            // Copy Attempt
            if (data.copy_attempt === "None Detected") { 
                copyAttemptElement.className = 'text-gray-500 text-lg font-bold';
            } else {
                copyAttemptElement.className = 'text-red-600 text-lg font-bold';
            }

            // Proctoring Alert - UI Class based on severity
            proctoringAlertElement.classList.remove('alert-critical', 'alert-warning');
            const isCriticalAlert = data.proctoring_alert && (data.proctoring_alert.includes("Alert") || data.proctoring_alert.includes("Cheating") || data.proctoring_alert.includes("Violation") || data.proctoring_alert.includes("Absent"));
            const isWarningAlert = data.proctoring_alert && (data.proctoring_alert.includes("Diverted") || data.proctoring_alert.includes("Drowsiness") || data.proctoring_alert.includes("Yawn"));
            
            if (isCriticalAlert) {
                proctoringAlertElement.classList.add('alert-critical');
            } else if (isWarningAlert) {
                proctoringAlertElement.classList.add('alert-warning');
            }

            // --- Handle Audible and Spoken Alerts ---
            const currentAlertType = data.alert_type; // This comes from the backend
            const currentTime = Date.now();

            // Log the incoming alert type for debugging
            console.log("Received alert_type from backend:", currentAlertType);

            if (currentAlertType && alertMessages[currentAlertType]) {
                const lastTime = lastAlertTimestamp.get(currentAlertType) || 0;

                // Trigger alert if it's a new type, or if it's the same type but enough time has passed
                if ((currentAlertType !== lastAlertTimestamp.get('lastTriggeredAlert') && currentAlertType !== lastAlertTimestamp.get('activeAlert')) || (currentTime - lastTime) > alertDebounceTime) {
                    console.log(`Triggering alert: ${currentAlertType}`);
                    playAlertSound();
                    speakAlert(alertMessages[currentAlertType]);
                    lastAlertTimestamp.set(currentAlertType, currentTime);
                    lastAlertTimestamp.set('lastTriggeredAlert', currentAlertType); // Track the last triggered alert type
                    // No need to set 'activeAlert' here, it's tracked implicitly by currentSpeakingUtterance
                } else {
                    console.log(`Debouncing alert: ${currentAlertType}. Time since last: ${currentTime - lastTime}ms`);
                }
            } else {
                // No active alert from backend, or alert type is not recognized. Stop existing alerts.
                stopAllAlerts();
                lastAlertTimestamp.set('lastTriggeredAlert', null); // Clear last triggered alert type
            }

        } catch (error) {
            console.error('Error fetching analytics:', error);
            // Optionally update UI to show error state for all fields
            sleepingStatusElement.textContent = 'Error fetching data';
            sleepingStatusElement.className = 'text-red-500 text-lg font-bold';
            unauthorizedActivityElement.textContent = 'Error';
            unauthorizedActivityElement.className = 'text-red-500 text-lg font-bold';
            copyAttemptElement.textContent = 'Error';
            copyAttemptElement.className = 'text-red-500 text-lg font-bold';
            proctoringAlertElement.textContent = 'Error';
            proctoringAlertElement.className = 'text-red-500 text-lg font-bold';
            stopAllAlerts(); // Stop alerts on error
        }
    }

    // --- Initialization ---
    // Set the video feed source
    videoFeedElement.src = "/video_feed";

    // Pre-load voices for faster speech synthesis (optional, but good practice)
    window.speechSynthesis.onvoiceschanged = () => {
        console.log("SpeechSynthesis voices loaded.");
    };

    // Initial fetch and then periodically fetch analytics data
    fetchAnalytics();
    setInterval(fetchAnalytics, ANALYTICS_REFRESH_INTERVAL);

    // --- Optional: Handle video feed loading errors ---
    videoFeedElement.onerror = () => {
        console.error("Failed to load video feed. Ensure the backend Flask server is running.");
        const videoContainer = videoFeedElement.parentElement;
        let errorMessage = videoContainer.querySelector('.video-error-message');
        if (!errorMessage) {
            errorMessage = document.createElement('p');
            errorMessage.className = 'video-error-message text-red-500 text-center mt-4 absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-gray-900 bg-opacity-75 p-4 rounded-lg';
            videoContainer.appendChild(errorMessage);
        }
        errorMessage.textContent = 'Video feed not available. Is the backend running?';
        stopAllAlerts(); // Stop alerts if video feed fails
    };
});
