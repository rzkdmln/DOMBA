// app/static/js/public/index.js

$(document).ready(function() {
    // Init DataTable
    const table = $('#dataTable').DataTable({
        "language": {
            "url": "/static/vendor/datatables/id.json",
            "info": "_START_-_END_ dari _TOTAL_",
            "paginate": {
                "previous": '<i class="fa-solid fa-chevron-left"></i>',
                "next": '<i class="fa-solid fa-chevron-right"></i>'
            }
        },
        "pageLength": 10,
        "order": [[1, "desc"]],
        "dom": '<"overflow-x-auto -mx-4 md:mx-0"t>p'
    });

    // Custom Search
    $('#custom-search').keyup(function() {
        table.search($(this).val()).draw();
    });

    // Custom Length
    $('#custom-length').change(function() {
        table.page.len($(this).val()).draw();
    });

    // Clock Update
    function updateClock() {
        const now = new Date();
        const time = now.toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false });
        const date = now.toLocaleDateString('id-ID', { day: '2-digit', month: 'long', year: 'numeric' });
        $('#current-time-display').text(time + ' WIB');
        $('#current-date-display').text(date);
    }

    function setTimeIcon() {
        const now = new Date();
        const hour = now.getHours();
        const card = $('.stats-card.lg\\:col-span-2');
        
        let icon = 'fa-sun';
        let iconColor = '#fbbf24';
        let gradientClass = 'from-blue-600 to-blue-700';
        
        if (hour >= 6 && hour < 12) {
            icon = 'fa-sun';
            iconColor = '#fbbf24';
            gradientClass = 'from-blue-600 to-amber-500';
        } else if (hour >= 12 && hour < 18) {
            icon = 'fa-sun';
            iconColor = '#f97316';
            gradientClass = 'from-blue-600 to-orange-400';
        } else if (hour >= 18 && hour < 21) {
            icon = 'fa-cloud-sun';
            iconColor = '#ef4444';
            gradientClass = 'from-blue-600 to-rose-500';
        } else {
            icon = 'fa-moon';
            iconColor = '#60a5fa';
            gradientClass = 'from-blue-600 to-indigo-950';
        }
        
        $('#time-icon i').removeClass().addClass('fas ' + icon).css({
            'color': iconColor,
            'opacity': '1',
            'text-shadow': '0 0 15px ' + iconColor + '80'
        });
        
        card.removeClass('bg-blue-600 from-blue-600 to-blue-700 to-amber-500 to-orange-400 to-rose-500 to-indigo-950')
            .addClass('bg-gradient-to-r ' + gradientClass);
            
        // Remove the old time-bg decorator since we're using a full card gradient now
        $('.time-bg').addClass('hidden');
    }

    updateClock();
    setTimeIcon();

    // Reveal Animation on Scroll
    function reveal() {
        var reveals = document.querySelectorAll(".reveal");
        for (var i = 0; i < reveals.length; i++) {
            var windowHeight = window.innerHeight;
            var elementTop = reveals[i].getBoundingClientRect().top;
            var elementVisible = 150;
            if (elementTop < windowHeight - elementVisible) {
                reveals[i].classList.add("active");
            }
        }
    }
    window.addEventListener("scroll", reveal);
    reveal(); // Run once on load

    // Map Initialization
    const map = L.map('map', { scrollWheelZoom: false }).setView([-7.2274, 107.9087], 11);
    L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; OpenStreetMap contributors &copy; CARTO'
    }).addTo(map);

    // Remove attribution control
    map.attributionControl.remove();

    let markers = [];
    let activeFilters = [];

    // Mobile map interaction state
    let mapInteractionEnabled = false;
    let lastTapTime = 0;
    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) || window.innerWidth < 1024;

    // Fade out instruction overlay on map interaction
    const mapInstruction = document.getElementById('mapInstruction');
    if (mapInstruction) {
        let hasInteracted = false;

        function fadeOutInstruction() {
            if (!hasInteracted) {
                hasInteracted = true;
                mapInstruction.style.opacity = '0';
                setTimeout(() => {
                    mapInstruction.style.display = 'none';
                }, 500);
            }
        }

        // Listen for map movement events
        map.on('movestart', fadeOutInstruction);
        map.on('zoomstart', fadeOutInstruction);
        map.on('dragstart', fadeOutInstruction);

        // Also fade out on touch/click for mobile
        if (isMobile) {
            map.on('click', fadeOutInstruction);
        }
    }

    function escapeHtml(unsafe) {
        return String(unsafe)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    function makeGoogleMapsDirectionsUrl(lat, lng) {
        const url = new URL('https://www.google.com/maps/dir/');
        url.searchParams.set('api', '1');
        url.searchParams.set('destination', `${lat},${lng}`);
        url.searchParams.set('travelmode', 'driving');
        url.searchParams.set('dir_action', 'navigate');
        return url.toString();
    }

    // Load GeoJSON and calculate centroids
    let kecamatanCoords = {};
    let googleMapsCoords = {}; // Koordinat presisi hanya untuk Google Maps link

    function loadGoogleMapsCoords() {
        return fetch('/static/data/kantor_kecamatan_overrides.json')
            .then(r => (r.ok ? r.json() : null))
            .then(data => {
                if (data && typeof data === 'object') {
                    // Ambil semua key kecuali 'comment'
                    for (const [key, coords] of Object.entries(data)) {
                        if (key !== 'comment' && Array.isArray(coords) && coords.length === 2) {
                            googleMapsCoords[key] = coords;
                        }
                    }
                }
            })
            .catch(() => {
                // optional file; ignore errors
            });
    }

    function getGoogleMapsCoords(name, cleanName) {
        if (name && googleMapsCoords[name]) return googleMapsCoords[name];
        if (cleanName && googleMapsCoords[cleanName]) return googleMapsCoords[cleanName];
        return null;
    }

    function normalizeKecamatanName(cleanName) {
        if (!cleanName) return cleanName;
        const trimmed = String(cleanName).trim();
        // GeoJSON memakai singkatan "Bl. Limbangan"
        if (/^(blubur|balubur)\s+limbangan$/i.test(trimmed)) return 'Bl. Limbangan';
        return trimmed;
    }

    fetch('/static/data/garut_kecamatan.geojson')
        .then(response => response.json())
        .then(data => {
            data.features.forEach(feature => {
                const name = feature.properties.nm_kecamatan;
                const centroid = turf.centroid(feature);
                const coords = centroid.geometry.coordinates;
                kecamatanCoords[name] = [coords[1], coords[0]]; // Leaflet uses [lat, lng]
            });
            // Load optional Google Maps overrides, then place markers
            return loadGoogleMapsCoords().finally(() => placeMarkers());
        })
        .catch(error => {
            console.error('Error loading GeoJSON:', error);
            // Fallback to approximate coordinates
            kecamatanCoords = {
                "Garut Kota": [-7.2211, 107.9048],
                "Tarogong Kidul": [-7.2274, 107.8927],
                "Tarogong Kaler": [-7.1754, 107.8867],
                "Karangpawitan": [-7.2054, 107.9467],
                "Wanaraja": [-7.1754, 107.9767],
                "Banyuresmi": [-7.1554, 107.9167],
                "Samarang": [-7.2454, 107.8367],
                "Pasirwangi": [-7.2254, 107.7867],
                "Leles": [-7.1154, 107.8967],
                "Kadungora": [-7.0854, 107.8867],
                "Leuwigoong": [-7.1054, 107.9367],
                "Cibatu": [-7.0954, 107.9667],
                "Kersamanah": [-7.0554, 108.0167],
                "Malangbong": [-7.0654, 108.1067],
                "Sukawening": [-7.1354, 107.9967],
                "Karangtengah": [-7.1554, 108.0567],
                "Bayongbong": [-7.2754, 107.8767],
                "Cigedug": [-7.2954, 107.8467],
                "Cilawu": [-7.2654, 107.9367],
                "Cisurupan": [-7.3254, 107.8167],
                "Sukaresmi": [-7.3054, 107.7667],
                "Cikajang": [-7.3754, 107.8667],
                "Banjarwangi": [-7.4354, 107.9167],
                "Singajaya": [-7.4854, 107.9767],
                "Peundeuy": [-7.5354, 107.9967],
                "Cihurip": [-7.4654, 107.8867],
                "Pakenjeng": [-7.4854, 107.7567],
                "Cisewu": [-7.3854, 107.5167],
                "Caringin": [-7.4354, 107.5667],
                "Talegong": [-7.3054, 107.5567],
                "Bungbulang": [-7.4854, 107.6167],
                "Mekarmukti": [-7.5454, 107.5667],
                "Pamulihan": [-7.4054, 107.7167],
                "Pameungpeuk": [-7.6554, 107.7867],
                "Cibalong": [-7.6754, 107.8667],
                "Cikelet": [-7.6354, 107.7167],
                "Sucinaraja": [-7.1654, 107.9667],
                "Pangatikan": [-7.1454, 107.9767],
                "Selaawi": [-7.0254, 108.0067],
                "Cibiuk": [-7.0854, 107.9267],
                "Bl. Limbangan": [-7.0354, 107.9567]
            };
            loadGoogleMapsCoords().finally(() => placeMarkers());
        });

    function placeMarkers() {
        // Clear existing markers if any
        markers.forEach(m => map.removeLayer(m.marker));
        markers = [];

        // Dynamic Markers from Stock Data
        const stockData = JSON.parse(document.getElementById('map').dataset.stock);

        stockData.forEach(function(item) {
            const name = item.nama_kecamatan;
            let cleanName = name.replace(/^Kecamatan\s+/, '').replace(/^Dinas$/, 'Garut Kota');
            cleanName = normalizeKecamatanName(cleanName);
            const stock = item.jumlah_ktp;
            const lastUpdated = item.last_updated;
            
            // Koordinat untuk marker peta (centroid GeoJSON lama, tetap)
            let coords;
            if (name === 'Dinas') {
                // Dinas di Jl. Patriot No. 12-14, Sukagalih, Kec. Tarogong Kidul
                coords = [-7.2018056, 107.8852278];
            } else {
                coords = kecamatanCoords[cleanName];
                if (!coords) {
                    coords = [-7.2274 + (Math.random() - 0.5) * 0.1, 107.9087 + (Math.random() - 0.5) * 0.1];
                }
            }

            // Koordinat untuk Google Maps link (presisi, dari override)
            let googleMapsCoord = getGoogleMapsCoords(name, cleanName) || coords;
            
            let color = '#10b981'; // green
            let category = 'tersedia';
            if (stock === 0) {
                color = '#f43f5e'; // red
                category = 'habis';
            } else if (stock <= 20) {
                color = '#f59e0b'; // amber
                category = 'terbatas';
            }

            const marker = L.circleMarker(coords, {
                radius: 12,
                fillColor: color,
                color: '#fff',
                weight: 3,
                opacity: 1,
                fillOpacity: 0.8,
                className: `map-stock-marker map-stock-marker--${category}`
            });

            const safeName = escapeHtml(name);
            const directionsUrl = makeGoogleMapsDirectionsUrl(googleMapsCoord[0], googleMapsCoord[1]);

            marker.bindTooltip(
                `
                <div class="domba-tooltip">
                    <div class="domba-tooltip__title">${safeName}</div>
                    <div class="domba-tooltip__meta">Stok KTP-el: <span class="domba-tooltip__stock">${escapeHtml(stock)}</span></div>
                </div>
                `,
                {
                    direction: 'top',
                    sticky: true,
                    opacity: 1,
                    offset: [0, -10],
                    className: 'domba-map-tooltip'
                }
            );

            marker.bindPopup(`
                <div class="w-80 bg-white rounded-2xl border border-slate-100 shadow-lg shadow-slate-200/50">
                    <!-- Header -->
                    <div class="px-5 pt-5 pb-3 border-b border-slate-100">
                        <div class="text-lg font-black text-slate-900 truncate">${safeName}</div>
                    </div>

                    <!-- Info Grid -->
                    <div class="px-5 py-4 space-y-3">
                        <!-- Stok -->
                        <div class="flex items-center justify-between">
                            <div class="flex items-center gap-2">
                                <div class="w-8 h-8 bg-blue-50 rounded-lg flex items-center justify-center text-blue-600 text-xs">
                                    <i class="fa-solid fa-box"></i>
                                </div>
                                <span class="text-[0.7rem] font-bold text-slate-500 uppercase tracking-tight">Stok</span>
                            </div>
                            <span class="text-base font-black text-slate-800">${escapeHtml(stock)}</span>
                        </div>

                        <!-- Status -->
                        <div class="flex items-center justify-between">
                            <div class="flex items-center gap-2">
                                <div class="w-8 h-8 rounded-lg flex items-center justify-center text-white text-xs font-black" style="background-color: ${color};">
                                    <i class="fa-solid ${category === 'tersedia' ? 'fa-check' : category === 'terbatas' ? 'fa-exclamation' : 'fa-xmark'}"></i>
                                </div>
                                <span class="text-[0.7rem] font-bold text-slate-500 uppercase tracking-tight">Status</span>
                            </div>
                            <div class="inline-flex items-center gap-1 px-2 py-1 rounded-lg text-[0.65rem] font-black uppercase tracking-wider" style="background-color: ${category === 'tersedia' ? '#ecfdf5' : category === 'terbatas' ? '#fffbeb' : '#fef2f2'}; color: ${category === 'tersedia' ? '#059669' : category === 'terbatas' ? '#b45309' : '#991b1b'};">
                                ${category === 'tersedia' ? 'Tersedia' : category === 'terbatas' ? 'Terbatas' : 'Habis'}
                            </div>
                        </div>

                        <!-- Last Update -->
                        ${lastUpdated ? `
                        <div class="flex items-center justify-between">
                            <div class="flex items-center gap-2">
                                <div class="w-8 h-8 bg-slate-100 rounded-lg flex items-center justify-center text-slate-600 text-xs">
                                    <i class="fa-solid fa-clock"></i>
                                </div>
                                <span class="text-[0.7rem] font-bold text-slate-500 uppercase tracking-tight">Update</span>
                            </div>
                            <span class="text-[0.75rem] font-bold text-slate-700">${escapeHtml(lastUpdated)}</span>
                        </div>
                        ` : ''}
                    </div>

                    <!-- Action Buttons -->
                    <div class="px-5 pb-5 pt-2 flex gap-2">
                        <a href="${directionsUrl}" target="_blank" rel="noopener noreferrer" class="flex-1 inline-flex items-center justify-center gap-1.5 px-3 py-2.5 bg-blue-50 hover:bg-blue-100 text-blue-600 rounded-lg text-[0.7rem] font-black transition-all border border-blue-200 active:bg-blue-200">
                            <i class="fa-solid fa-route text-xs"></i>
                            <span>Rute</span>
                        </a>
                        <a href="https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(googleMapsCoord[0] + ',' + googleMapsCoord[1])}" target="_blank" rel="noopener noreferrer" class="flex-1 inline-flex items-center justify-center gap-1.5 px-3 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-[0.7rem] font-black transition-all border border-slate-200 active:bg-slate-300">
                            <i class="fa-solid fa-map-pin text-xs"></i>
                            <span>Peta</span>
                        </a>
                    </div>
                </div>
            `, { maxWidth: 340, className: 'domba-popup' });

            const normalStyle = {
                radius: 12,
                weight: 3,
                fillOpacity: 0.8
            };
            const hoverStyle = {
                radius: 16,
                weight: 4,
                fillOpacity: 0.95
            };

            marker.on('mouseover', function() {
                this.setStyle(hoverStyle);
                try { this.bringToFront(); } catch (e) {}
                this.openTooltip();
            });
            marker.on('mouseout', function() {
                this.setStyle(normalStyle);
                this.closeTooltip();
            });
            marker.on('touchstart', function() {
                this.setStyle(hoverStyle);
                this.openTooltip();
            });
            marker.on('touchend', function() {
                // Biarkan popup tetap dominan; tooltip ditutup saat selesai sentuh
                if (!this.isPopupOpen || !this.isPopupOpen()) {
                    this.setStyle(normalStyle);
                }
                this.closeTooltip();
            });
            marker.on('popupopen', function() {
                this.setStyle(hoverStyle);
            });
            marker.on('popupclose', function() {
                this.setStyle(normalStyle);
            });

            markers.push({
                marker: marker,
                category: category
            });
            
            marker.addTo(map);
        });
    }

    // Filter Logic
    $('.filter-btn').click(function() {
        const filter = $(this).data('filter');
        const index = activeFilters.indexOf(filter);

        if (index > -1) {
            activeFilters.splice(index, 1);
            $(this).removeClass('ring-4 ring-blue-500/20 border-blue-200 bg-blue-50/30');
        } else {
            activeFilters.push(filter);
            $(this).addClass('ring-4 ring-blue-500/20 border-blue-200 bg-blue-50/30');
        }

        updateMarkersVisibility();
    });

    function updateMarkersVisibility() {
        markers.forEach(item => {
            if (activeFilters.length === 0 || activeFilters.includes(item.category)) {
                if (!map.hasLayer(item.marker)) {
                    item.marker.addTo(map);
                }
            } else {
                if (map.hasLayer(item.marker)) {
                    map.removeLayer(item.marker);
                }
            }
        });
    }

    // Scroll to Top Button Functionality
    const scrollToTopBtn = document.getElementById('scrollToTopBtn');

    // Show/hide button based on scroll position
    window.addEventListener('scroll', function() {
        if (window.pageYOffset > 300) { // Show after scrolling 300px
            scrollToTopBtn.classList.add('show');
            scrollToTopBtn.style.display = 'block';
        } else {
            scrollToTopBtn.classList.remove('show');
            setTimeout(() => {
                if (!scrollToTopBtn.classList.contains('show')) {
                    scrollToTopBtn.style.display = 'none';
                }
            }, 300); // Match transition duration
        }
    });

    // Scroll to top when button is clicked
    scrollToTopBtn.addEventListener('click', function() {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });

});
