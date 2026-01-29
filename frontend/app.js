// ==================== BigMusic App Premium ====================

class BigMusicApp {
    constructor() {
        this.apiUrl = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
            ? 'http://localhost:8000'
            : '';
        this.tracks = [];
        this.currentTrack = null;
        this.currentTrackIndex = -1;
        this.isPlaying = false;
        this.preloadedTracks = new Set(); // Для отслеживания уже предзагруженных треков

        this.init();
    }

    async init() {
        this.audioPlayer = document.getElementById('audioPlayer');
        this.initElements();
        this.initEventListeners();
        console.log('App initialized. Fetching initial tracks...');
        await this.loadTracks();
    }

    initElements() {
        this.tracksGrid = document.getElementById('tracksGrid');
        this.artistProfile = document.getElementById('artistProfile');
        this.loadingState = document.getElementById('loadingState');
        this.emptyState = document.getElementById('emptyState');
        this.trackCount = document.getElementById('trackCount');
        this.searchInput = document.getElementById('searchInput');
        this.refreshBtn = document.getElementById('refreshBtn');

        // Modal
        this.downloadModal = document.getElementById('downloadModal');
        this.downloadProgressBar = document.getElementById('downloadProgressBar');
        this.downloadStatus = document.getElementById('downloadStatus');

        // Player
        this.nowPlayingBar = document.getElementById('nowPlayingBar');
        this.nowPlayingCover = document.getElementById('nowPlayingCover');
        this.nowPlayingTitle = document.getElementById('nowPlayingTitle');
        this.nowPlayingArtist = document.getElementById('nowPlayingArtist');
        this.progressContainer = document.getElementById('progressContainer');
        this.progressBar = document.getElementById('progressBar');
        this.currentTimeEl = document.getElementById('currentTime');
        this.totalTimeEl = document.getElementById('totalTime');
        this.playPauseBtn = document.getElementById('playPauseBtn');
        this.prevBtn = document.getElementById('prevBtn');
        this.nextBtn = document.getElementById('nextBtn');
        this.volumeSlider = document.getElementById('volumeSlider');
    }

    async loadTracks(query = null, isRecommendation = false) {
        if (!isRecommendation) this.showLoading();

        try {
            let url = `${this.apiUrl}/api/tracks`;
            if (query && query.trim()) {
                url += `?q=${encodeURIComponent(query.trim())}`;
            }

            const response = await fetch(url);
            const data = await response.json();

            if (isRecommendation) {
                // Если это рекомендации, добавляем их в конец текущего списка
                this.tracks = [...this.tracks, ...data.tracks];
            } else {
                this.tracks = data.tracks || [];
                this.renderArtistProfile(data.artist);
            }

            this.renderTracks();
            if (this.trackCount) this.trackCount.textContent = query ? this.tracks.length : "Top Hits";
        } catch (error) {
            console.error('Failed to load tracks:', error);
            if (!isRecommendation) this.showEmpty();
        } finally {
            this.hideLoading();
            if (this.tracksGrid) this.tracksGrid.style.opacity = '1';
        }
    }

    renderArtistProfile(artist) {
        if (!this.artistProfile) return;
        if (!artist) {
            this.artistProfile.classList.add('hidden');
            return;
        }
        this.artistProfile.innerHTML = `
            <img class="artist-img animate-scale-in" src="${artist.image_url || ''}" alt="">
            <div class="artist-info-main animate-fade-in">
                <div class="artist-meta">ПОДТВЕРЖДЕННЫЙ ИСПОЛНИТЕЛЬ</div>
                <div class="artist-name">${artist.name}</div>
                <div class="artist-stats">${this.formatNumber(artist.followers)} слушателей за месяц</div>
            </div>
        `;
        this.artistProfile.classList.remove('hidden');
    }

    initEventListeners() {
        let timeout;
        if (this.searchInput) {
            this.searchInput.addEventListener('input', (e) => {
                clearTimeout(timeout);
                timeout = setTimeout(() => this.loadTracks(e.target.value), 500);
            });
        }

        if (this.refreshBtn) {
            this.refreshBtn.addEventListener('click', () => this.loadTracks(this.searchInput?.value));
        }

        this.playPauseBtn?.addEventListener('click', () => this.togglePlayPause());
        this.prevBtn?.addEventListener('click', () => this.playPrev());
        this.nextBtn?.addEventListener('click', () => this.playNext());

        this.progressContainer?.addEventListener('click', (e) => {
            const rect = this.progressContainer.getBoundingClientRect();
            const pos = (e.clientX - rect.left) / rect.width;
            if (this.audioPlayer?.duration) {
                this.audioPlayer.currentTime = pos * this.audioPlayer.duration;
            }
        });

        this.volumeSlider?.addEventListener('input', (e) => {
            if (this.audioPlayer) this.audioPlayer.volume = e.target.value / 100;
        });

        this.audioPlayer?.addEventListener('timeupdate', () => {
            if (this.audioPlayer.duration) {
                const percent = (this.audioPlayer.currentTime / this.audioPlayer.duration) * 100;
                if (this.progressBar) this.progressBar.style.width = `${percent}%`;
                if (this.currentTimeEl) this.currentTimeEl.textContent = this.formatTime(this.audioPlayer.currentTime);

                // --- ПРЕДЗАГРУЗКА ---
                // Если осталось 30 секунд до конца, загружаем следующий трек на сервер
                if (this.audioPlayer.duration - this.audioPlayer.currentTime < 30) {
                    this.preloadNextTrack();
                }
            }
        });

        this.audioPlayer?.addEventListener('loadedmetadata', () => {
            if (this.totalTimeEl) this.totalTimeEl.textContent = this.formatTime(this.audioPlayer.duration);
        });

        this.audioPlayer?.addEventListener('ended', () => this.playNext());
    }

    async preloadNextTrack() {
        const nextIndex = this.currentTrackIndex + 1;
        if (nextIndex < this.tracks.length) {
            const nextTrack = this.tracks[nextIndex];
            if (!this.preloadedTracks.has(nextTrack.id)) {
                this.preloadedTracks.add(nextTrack.id);
                console.log('Preloading next track to server:', nextTrack.title);
                // Тихий запрос на стриминг, чтобы сервер начал скачивание
                fetch(`${this.apiUrl}/api/stream/${nextTrack.id}`).catch(() => { });
            }
        }

        // --- РЕКОМЕНДАЦИИ ---
        // Если мы подходим к концу текущего списка (осталось 2 трека), подгружаем похожие
        if (this.tracks.length - 1 - this.currentTrackIndex <= 2) {
            this.loadRecommendations();
        }
    }

    async loadRecommendations() {
        if (this.isLoadingRecs || !this.currentTrack) return;
        this.isLoadingRecs = true;
        console.log('Loading style-based recommendations...');

        try {
            const resp = await fetch(`${this.apiUrl}/api/tracks?seed_track=${this.currentTrack.id}`);
            const data = await resp.json();
            if (data.tracks && data.tracks.length > 0) {
                // Добавляем только те, которых нет в списке
                const newTracks = data.tracks.filter(nt => !this.tracks.find(t => t.id === nt.id));
                this.tracks = [...this.tracks, ...newTracks];
                this.renderTracks();
                console.log('Added ' + newTracks.length + ' similar tracks to queue');
            }
        } catch (e) {
            console.error('Recommendations fail:', e);
        } finally {
            this.isLoadingRecs = false;
        }
    }

    renderTracks() {
        if (!this.tracksGrid) return;
        if (this.tracks.length === 0) { this.showEmpty(); return; }
        this.hideLoading();
        this.emptyState.classList.add('hidden');

        this.tracksGrid.innerHTML = this.tracks.map((track, index) => `
            <div class="track-card animate-fade-in ${this.currentTrack?.id === track.id ? 'playing' : ''}" style="animation-delay: ${index * 0.05}s">
                <div class="track-cover-wrapper">
                    <img class="track-cover" src="${track.cover_url || ''}" alt="">
                    <div class="overlay-actions">
                        <button class="card-btn play-card-btn" onclick="app.playTrack(${index})">
                            <svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
                        </button>
                        <button class="card-btn download-card-btn" onclick="app.downloadTrack('${track.id}')">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M7 10l5 5 5-5M12 15V3"/></svg>
                        </button>
                    </div>
                </div>
                <div class="track-info">
                    <div class="track-title">${this.escapeHtml(track.title)}</div>
                    <div class="track-artist clickable-artist" onclick="app.searchArtistName('${this.escapeHtml(track.artist)}')">${this.escapeHtml(track.artist)}</div>
                </div>
            </div>
        `).join('');
    }

    searchArtistName(name) {
        const firstName = name.split(',')[0].trim();
        if (this.searchInput) this.searchInput.value = firstName;
        this.loadTracks(firstName);
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    async playTrack(index) {
        if (index < 0 || index >= this.tracks.length) return;
        const track = this.tracks[index];

        try {
            const checkResp = await fetch(`${this.apiUrl}/api/check/${track.id}`);
            const status = await checkResp.json();

            if (!status.ready) {
                this.showDownloadModal();
                this.updateDownloadProgress(5, 'Подготовка потока...');
                let currentProgress = 5;
                const interval = setInterval(() => {
                    currentProgress += Math.random() * 5;
                    if (currentProgress > 99) currentProgress = 99;
                    this.updateDownloadProgress(currentProgress, 'Кэширование...');
                }, 300);

                await fetch(`${this.apiUrl}/api/stream/${track.id}`);
                clearInterval(interval);
                this.updateDownloadProgress(100, 'Готово!');
                setTimeout(() => this.hideDownloadModal(), 600);
            }
        } catch (e) { console.error('Check fail:', e); }

        this.currentTrack = track;
        this.currentTrackIndex = index;
        if (this.nowPlayingBar) {
            this.nowPlayingBar.classList.remove('hidden');
            if (this.nowPlayingCover) this.nowPlayingCover.src = track.cover_url || '';
            if (this.nowPlayingTitle) this.nowPlayingTitle.textContent = track.title;
            if (this.nowPlayingArtist) this.nowPlayingArtist.textContent = track.artist;
        }
        document.querySelectorAll('.track-card').forEach((c, i) => c.classList.toggle('playing', i === index));

        try {
            this.audioPlayer.src = `${this.apiUrl}/api/stream/${track.id}`;
            await this.audioPlayer.play();
            this.isPlaying = true;
            this.updatePlayPauseButton();
        } catch (e) { console.error('Play fail:', e); }
    }

    playNext() { this.playTrack(this.currentTrackIndex + 1); }
    playPrev() { this.playTrack(this.currentTrackIndex - 1); }

    showDownloadModal() { this.downloadModal?.classList.remove('hidden'); }
    hideDownloadModal() { this.downloadModal?.classList.add('hidden'); }
    updateDownloadProgress(percent, status) {
        if (this.downloadProgressBar) this.downloadProgressBar.style.width = `${percent}%`;
        if (status && this.downloadStatus) this.downloadStatus.textContent = status;
    }

    togglePlayPause() {
        if (!this.currentTrack || !this.audioPlayer) return;
        if (this.isPlaying) this.audioPlayer.pause();
        else this.audioPlayer.play();
        this.isPlaying = !this.isPlaying;
        this.updatePlayPauseButton();
    }

    updatePlayPauseButton() {
        const play = this.playPauseBtn?.querySelector('.play-icon');
        const pause = this.playPauseBtn?.querySelector('.pause-icon');
        play?.classList.toggle('hidden', this.isPlaying);
        pause?.classList.toggle('hidden', !this.isPlaying);
    }

    async downloadTrack(id) { window.open(`${this.apiUrl}/api/download/${id}`, "_blank"); }
    formatTime(s) {
        if (!s || isNaN(s)) return '0:00';
        const m = Math.floor(s / 60); const sec = Math.floor(s % 60);
        return `${m}:${sec.toString().padStart(2, '0')}`;
    }
    formatNumber(n) { return new Intl.NumberFormat('ru-RU').format(n); }
    showLoading() { if (this.loadingState) this.loadingState.classList.remove('hidden'); }
    hideLoading() { if (this.loadingState) this.loadingState.classList.add('hidden'); }
    showEmpty() { this.hideLoading(); this.emptyState?.classList.remove('hidden'); }
    escapeHtml(t) { const d = document.createElement('div'); d.textContent = t; return d.innerHTML; }
}

let app;
document.addEventListener('DOMContentLoaded', () => {
    app = new BigMusicApp();
    window.app = app;
});
