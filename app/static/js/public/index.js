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

    let markers = [];
    let activeFilters = [];

    // Load GeoJSON and calculate centroids
    let kecamatanCoords = {};
    fetch('/static/data/garut_kecamatan.geojson')
        .then(response => response.json())
        .then(data => {
            data.features.forEach(feature => {
                const name = feature.properties.nm_kecamatan;
                const centroid = turf.centroid(feature);
                const coords = centroid.geometry.coordinates;
                kecamatanCoords[name] = [coords[1], coords[0]]; // Leaflet uses [lat, lng]
            });
            // Now place markers
            placeMarkers();
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
            placeMarkers();
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
            const stock = item.jumlah_ktp;
            
            let coords;
            if (name === 'Dinas') {
                coords = [-7.2018145, 107.8852168];
            } else {
                coords = kecamatanCoords[cleanName];
                if (!coords) {
                    coords = [-7.2274 + (Math.random() - 0.5) * 0.1, 107.9087 + (Math.random() - 0.5) * 0.1];
                }
            }
            
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
                fillOpacity: 0.8
            });

            marker.bindPopup(`
                <div class="p-3">
                    <div class="text-[0.6rem] font-bold text-slate-400 uppercase tracking-widest mb-1">Wilayah</div>
                    <div class="text-lg font-black text-slate-800 mb-3">${name}</div>
                    <div class="flex items-center gap-3">
                        <div class="px-3 py-1 bg-slate-100 rounded-lg text-xs font-bold text-slate-600">
                            Stok: <span class="text-blue-600">${stock}</span>
                        </div>
                        <div class="w-2 h-2 rounded-full" style="background-color: ${color}"></div>
                    </div>
                </div>
            `);

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
