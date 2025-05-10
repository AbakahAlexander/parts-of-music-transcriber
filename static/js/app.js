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
        const fileName = musicFileInput.files[0]?.name || 'No file chosen';
        const fileLabel = musicFileInput.nextElementSibling;
        fileLabel.textContent = fileName;
        
        // Validate file is MP3
        const file = musicFileInput.files[0];
        if (file && !file.name.toLowerCase().endsWith('.mp3')) {
            alert('Please select an MP3 file');
            musicFileInput.value = '';
            fileLabel.textContent = 'Choose MP3 file';
        }
    });
    
    // Functions
    async function handleFileUpload(e) {
        e.preventDefault();
        
        const file = musicFileInput.files[0];
        if (!file) {
            alert('Please select an MP3 file to upload');
            return;
        }
        
        if (!file.name.toLowerCase().endsWith('.mp3')) {
            alert('Only MP3 files are supported');
            return;
        }
        
        // Show progress
        uploadBtn.disabled = true;
        progressContainer.classList.remove('hidden');
        progressStatus.textContent = 'Processing...';
        
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
            resultsSection.classList.remove('hidden');
            
            // Load the score
            switchTab('score');
            
        } catch (error) {
            progressStatus.textContent = `Error: ${error.message}`;
            console.error('Upload error:', error);
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
                        const svg = verovioToolkit.renderToSVG(1, {});
                        notationView.innerHTML = svg;
                    } else {
                        notationView.innerHTML = '<p>Music notation viewer not available.</p>';
                    }
                })
                .catch(error => {
                    console.error('Error loading notation:', error);
                    notationView.innerHTML = `<p>Error loading notation: ${error.message}</p>`;
                });
        } else {
            notationView.innerHTML = `<p>File format not supported for display: ${filePath}</p>`;
        }
    }
    
    function setupAudioPlayer(part) {
        // Check if we have an audio file for this part
        const audioKey = `${part}_audio`;
        if (!resultFiles || !resultFiles[audioKey]) {
            // Try to use MIDI file instead
            if (resultFiles[`${part}_midi`]) {
                notationView.insertAdjacentHTML('afterend', 
                    `<p class="note">Audio conversion not available. Using MIDI playback which may not work in all browsers.</p>`
                );
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
            alert('No audio available for this part');
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
                    alert(`Error playing audio: ${error.message}`);
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
            return;
        }
        
        // Fall back to MusicXML if audio not available
        if (!resultFiles || !resultFiles[currentPart]) {
            alert('No file available for this part.');
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
    }
});
