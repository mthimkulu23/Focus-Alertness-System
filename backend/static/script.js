document.addEventListener('DOMContentLoaded', () => {
    const videoFeedElement = document.getElementById('videoFeed');
    const faceCountElement = document.getElementById('faceCount');
    const sleepingStatusElement = document.getElementById('sleepingStatus');
    const focusScoreElement = document.getElementById('focusScore');
    // New analytics elements (matching IDs from index.html)
    const unauthorizedActivityElement = document.getElementById('unauthorizedActivity');
    const copyAttemptElement = document.getElementById('copyAttempt');
    const proctoringAlertElement = document.getElementById('proctoringAlert');

    // --- Configure Endpoints ---
    const VIDEO_FEED_URL = 'http://127.0.0.1:5000/video_feed'; // Flask video stream
    const ANALYTICS_URL = 'http://127.0.0.1:5000/analytics';   // Flask analytics endpoint
    const ANALYTICS_REFRESH_INTERVAL = 2000; // Refresh analytics every 2 seconds (2000 ms)

    // --- Start Video Feed ---
    // Simply setting the src of the <img> tag to the MJPEG stream endpoint
    // The browser will handle decoding the MJPEG stream.
    videoFeedElement.src = VIDEO_FEED_URL;

    // --- Function to Fetch and Update Analytics ---
    async function fetchAnalytics() {
        try {
            const response = await fetch(ANALYTICS_URL);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();

            // Update UI elements with fetched data
            faceCountElement.textContent = data.face_count;
            sleepingStatusElement.textContent = data.sleeping_status;
            focusScoreElement.textContent = data.focus_score.toFixed(2); // Format to 2 decimal places
            // Update new analytics fields
            unauthorizedActivityElement.textContent = data.unauthorized_activity;
            copyAttemptElement.textContent = data.copy_attempt;
            proctoringAlertElement.textContent = data.proctoring_alert;

            // Update status text color based on sleeping status (simple logic)
            if (data.sleeping_status.includes("sleeping")) {
                sleepingStatusElement.className = 'text-red-600 text-lg font-bold';
            } else if (data.sleeping_status.includes("No person")) {
                 sleepingStatusElement.className = 'text-gray-500 text-lg font-bold';
            }
            else {
                sleepingStatusElement.className = 'text-green-600 text-lg font-bold';
            }

            // Update colors for new alert statuses
            // Unauthorized Activity
            if (data.unauthorized_activity === "None Detected" || data.unauthorized_activity === "No person detected") {
                unauthorizedActivityElement.className = 'text-gray-500 text-lg font-bold';
            } else {
                unauthorizedActivityElement.className = 'text-red-600 text-lg font-bold';
            }

            // Copy Attempt
            if (data.copy_attempt === "None Detected" || data.copy_attempt === "No person detected") {
                copyAttemptElement.className = 'text-gray-500 text-lg font-bold';
            } else {
                copyAttemptElement.className = 'text-red-600 text-lg font-bold';
            }

            // Proctoring Alert
            if (data.proctoring_alert === "No Violations") {
                proctoringAlertElement.className = 'text-green-600 text-lg font-bold';
            } else {
                proctoringAlertElement.className = 'text-red-600 text-lg font-bold';
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
        }
    }

    // --- Periodically Fetch Analytics ---
    // Call immediately on load and then set an interval
    fetchAnalytics();
    setInterval(fetchAnalytics, ANALYTICS_REFRESH_INTERVAL);

    // --- Optional: Handle video feed loading errors ---
    videoFeedElement.onerror = () => {
        console.error("Failed to load video feed. Ensure the backend Flask server is running at", VIDEO_FEED_URL);
        // You could display a message on the UI
        const videoContainer = videoFeedElement.parentElement;
        const errorMessage = document.createElement('p');
        errorMessage.textContent = 'Video feed not available. Is the backend running?';
        errorMessage.className = 'text-red-500 text-center mt-4';
        videoContainer.appendChild(errorMessage);
    };
});
