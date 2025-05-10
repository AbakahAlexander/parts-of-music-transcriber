document.addEventListener('DOMContentLoaded', () => {
    // Elements
    const uploadForm = document.getElementById('upload-form');
    const musicFileInput = document.getElementById('music-file');
    const uploadBtn = document.getElementById('upload-btn');
    const progressContainer = document.getElementById('progress-container');
    const progressStatus = document.getElementById('progress-status');
    const resultsSection = document.getElementById('results-section');
    const notationView = document.getElementById('notation-view');
    const playBtn = document.getElementById('play-btn');
    const stopBtn = document.getElementById('stop-btn');
    const downloadBtn = document.getElementById('download-btn');
    const tabButtons = document.querySelectorAll('.tab-button');
    
    // State
    let currentPart = 'score';
    let resultFiles = {};
    let verovioToolkit = null;
    let audioPlayer = null;
    let isPlaying = false;
    
    // Initialize Verovio toolkit
    try {
        verovioToolkit = new verovio.toolkit();
    } catch (e) {
        console.error('Error initializing Verovio toolkit:', e);
    }
    
    // Event listeners
    uploadForm.addEventListener('submit', handleFileUpload);
    tabButtons.forEach(button => {
        button.addEventListener('click', () => switchTab(button.dataset.part));
    });
    playBtn.addEventListener('click', playCurrentPart);
    stopBtn.addEventListener('click', stopPlayback);
    downloadBtn.addEventListener('click', downloadCurrentPart);
    
    // Display file name when selected
    musicFileInput.addEventListener('change', () => {
        const file = musicFileInput.files[0];
        const fileLabel = musicFileInput.nextElementSibling;
        
        if (file) {
            // Validate file is MP3
            if (!file.name.toLowerCase().endsWith('.mp3')) {
                showNotification('Only MP3 files are supported', 'error');
                musicFileInput.value = '';
                fileLabel.innerHTML = '<span class="icon">📁</span> Choose MP3 file';
                return;
            }
            
            fileLabel.innerHTML = `<span class="icon">🎵</span> ${file.name}`;
        } else {
            fileLabel.innerHTML = '<span class="icon">📁</span> Choose MP3 file';
        }
    });
    
    // Functions
    async function handleFileUpload(e) {
        e.preventDefault();
        
        const file = musicFileInput.files[0];
        if (!file) {
            showNotification('Please select an MP3 file', 'error');
            return;
        }
        
        if (!file.name.toLowerCase().endsWith('.mp3')) {
            showNotification('Only MP3 files are supported', 'error');
            return;
        }
        
        // Show progress
        uploadBtn.disabled = true;
        progressContainer.classList.remove('hidden');
        progressStatus.textContent = 'Processing your audio file...';
        
        const formData = new FormData();
        formData.append('file', file);
        
        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error ${response.status}`);
            }
            
            const data = await response.json();
            resultFiles = data.files;
            
            // Update UI
            progressStatus.textContent = 'Processing complete!';
            setTimeout(() => {
                progressContainer.classList.add('hidden');
                resultsSection.classList.remove('hidden');
                
                // Smoothly scroll to results
                resultsSection.scrollIntoView({ behavior: 'smooth' });
                
                // Load the score
                switchTab('score');
            }, 1000);
            
        } catch (error) {
            progressStatus.textContent = `Error: ${error.message}`;
            console.error('Upload error:', error);
            showNotification(`Error: ${error.message}`, 'error');
        } finally {
            uploadBtn.disabled = false;
        }
    }
    
    function switchTab(part) {
        currentPart = part;
        
        // Update active tab
        tabButtons.forEach(button => {
            if (button.dataset.part === part) {
                button.classList.add('active');
            } else {
                button.classList.remove('active');
            }
        });
        
        // Stop any current playback
        stopPlayback();
        
        // Show loading state
        notationView.innerHTML = `
            <div class="loading"></div>
            <p>Loading ${part} notation...</p>
        `;
        
        // Load the notation
        loadNotation(part);
        
        // Set up the audio player
        setupAudioPlayer(part);
    }
    
    function loadNotation(part) {
        if (!resultFiles || !resultFiles[part]) {
            notationView.innerHTML = '<p>No file available for this part.</p>';
            return;
        }
        
        const filePath = resultFiles[part];
        
        if (filePath.endsWith('.musicxml')) {
            // Load MusicXML with Verovio
            fetch(`/results/${filePath.split('/').pop()}`)
                .then(response => response.text())
                .then(xml => {
                    if (verovioToolkit) {
                        verovioToolkit.loadData(xml);
                        
                        // Configure rendering options
                        const options = {
                            adjustPageHeight: true,
                            scale: 40,
                            pageMarginTop: 50,
                            pageMarginLeft: 50,
                            pageMarginRight: 50,
                            pageMarginBottom: 50,
                            footer: 'none',
                            justifyVertically: false
                        };
                        
                        const svg = verovioToolkit.renderToSVG(1, options);
                        notationView.innerHTML = svg;
                        
                        // Make SVG responsive
                        const svgElement = notationView.querySelector('svg');
                        if (svgElement) {
                            svgElement.setAttribute('width', '100%');
                            svgElement.setAttribute('height', 'auto');
                            svgElement.style.maxWidth = '100%';
                        }
                    } else {
                        notationView.innerHTML = '<p>Music notation viewer not available.</p>';
                    }
                })
                .catch(error => {
                    console.error('Error loading notation:', error);
                    notationView.innerHTML = `<p>Error loading notation: ${error.message}</p>`;
                });
        } else {
            notationView.innerHTML = `
                <p>File format not supported for display: ${filePath.split('/').pop()}</p>
                <p>Click Play to listen to this part.</p>
            `;
        }
    }
    
    function setupAudioPlayer(part) {
        // Check if we have an audio file for this part
        const audioKey = `${part}_audio`;
        if (!resultFiles || !resultFiles[audioKey]) {
            // Try to use MIDI file instead
            if (resultFiles[`${part}_midi`]) {
                insertNotification('Audio conversion not available. Using MIDI playback which may not work in all browsers.', 'warning');
                return;
            }
            return;
        }
        
        // Create HTML5 audio element
        if (audioPlayer) {
            audioPlayer.pause();
            audioPlayer.remove();
        }
        
        audioPlayer = document.createElement('audio');
        audioPlayer.controls = false;
        audioPlayer.src = `/audio/${resultFiles[audioKey]}`;
        audioPlayer.style.display = 'none';
        document.body.appendChild(audioPlayer);
        
        // Set up event listeners
        audioPlayer.addEventListener('ended', () => {
            isPlaying = false;
            updatePlayButton();
        });
    }
    
    function playCurrentPart() {
        if (!audioPlayer) {
            showNotification('No audio available for this part', 'warning');
            return;
        }
        
        if (isPlaying) {
            audioPlayer.pause();
            isPlaying = false;
        } else {
            audioPlayer.play()
                .then(() => {
                    isPlaying = true;
                })
                .catch(error => {
                    console.error('Error playing audio:', error);
                    showNotification(`Error playing audio: ${error.message}`, 'error');
                });
        }
        
        updatePlayButton();
    }
    
    function stopPlayback() {
        if (audioPlayer) {
            audioPlayer.pause();
            audioPlayer.currentTime = 0;
            isPlaying = false;
            updatePlayButton();
        }
    }
    
    function updatePlayButton() {
        if (isPlaying) {
            playBtn.innerHTML = '<span class="icon">⏸</span> Pause';
        } else {
            playBtn.innerHTML = '<span class="icon">▶</span> Play';
        }
    }
    
    function downloadCurrentPart() {
        // First try to download audio
        const audioKey = `${currentPart}_audio`;
        if (resultFiles && resultFiles[audioKey]) {
            // Create a download link
            const a = document.createElement('a');
            a.href = `/audio/${resultFiles[audioKey]}`;
            a.download = resultFiles[audioKey];
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            
            showNotification(`Downloading ${currentPart} audio...`, 'success');
            return;
        }
        
        // Fall back to MusicXML if audio not available
        if (!resultFiles || !resultFiles[currentPart]) {
            showNotification('No file available for this part.', 'error');
            return;
        }
        
        const filePath = resultFiles[currentPart];
        const fileName = filePath.split('/').pop();
        
        // Create a download link
        const a = document.createElement('a');
        a.href = `/results/${fileName}`;
        a.download = fileName;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        
        showNotification(`Downloading ${currentPart} file...`, 'success');
    }
    
    function showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        
        // Style based on type
        switch(type) {
            case 'error':
                notification.style.backgroundColor = '#f44336';
                break;
            case 'success':
                notification.style.backgroundColor = '#4caf50';
                break;
            case 'warning':
                notification.style.backgroundColor = '#ff9800';
                break;
            default:
                notification.style.backgroundColor = '#2196f3';
        }
        
        // Apply common styles
        Object.assign(notification.style, {
            color: 'white',
            padding: '12px 16px',
            position: 'fixed',
            bottom: '20px',
            right: '20px',
            zIndex: '1000',
            borderRadius: '4px',
            boxShadow: '0 2px 5px rgba(0,0,0,0.2)',
            opacity: '0',
            transition: 'opacity 0.3s ease-in-out',
        });
        
        // Add to DOM and animate in
        document.body.appendChild(notification);
        setTimeout(() => notification.style.opacity = '1', 10);
        
        // Remove after 4 seconds
        setTimeout(() => {
            notification.style.opacity = '0';
            setTimeout(() => notification.remove(), 300);
        }, 4000);
    }
    
    function insertNotification(message, type = 'info') {
        // Remove any existing notification
        const existingNote = notationView.querySelector('.note');
        if (existingNote) {
            existingNote.remove();
        }
        
        // Create and insert notification
        const note = document.createElement('p');
        note.className = 'note';
        note.textContent = message;
        
        notationView.insertAdjacentElement('afterend', note);
    }
});
