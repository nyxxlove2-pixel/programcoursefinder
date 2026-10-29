// Map for marking a location (Settings > Location and the College profile).
// Clicking the map, dragging the pin, searching, or "Use my current location" fills the
// hidden latitude/longitude inputs and the address box, so nobody types coordinates.
// Map tiles and address search come from OpenStreetMap (free, no API key).

const PHILIPPINES = [12.88, 121.77];
const NOMINATIM = 'https://nominatim.openstreetmap.org';

// A pin drawn in the site's primary color, so no marker image files are needed
const PIN_ICON = L.divIcon({
  className: '',
  iconSize: [32, 40],
  iconAnchor: [16, 40],
  html: `<svg viewBox="0 0 32 40" width="32" height="40" aria-hidden="true">
           <path d="M16 0C7.2 0 0 7 0 15.7 0 27.5 16 40 16 40s16-12.5 16-24.3C32 7 24.8 0 16 0Z" fill="#4F46E5"/>
           <circle cx="16" cy="15.5" r="6" fill="#fff"/>
         </svg>`,
});

function setUpPicker(picker) {
  const latInput = document.getElementById(picker.dataset.latInput);
  const lngInput = document.getElementById(picker.dataset.lngInput);
  const addressInput = document.getElementById(picker.dataset.addressInput);
  const status = picker.querySelector('[data-map-status]');
  const searchInput = picker.querySelector('[data-map-search]');

  const map = L.map(picker.querySelector('[data-map]'), { scrollWheelZoom: false });
  L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    // OpenStreetMap blocks tile requests with no Referer. Django's default policy (same-origin)
    // sends none to other sites, so share just our site's address with the tile server.
    referrerPolicy: 'strict-origin-when-cross-origin',
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
  }).addTo(map);
  let marker = null;

  // Put the pin at a spot and save it in the hidden inputs (the model keeps 6 decimals)
  function placePin(lat, lng) {
    latInput.value = Number(lat).toFixed(6);
    lngInput.value = Number(lng).toFixed(6);
    if (!marker) {
      marker = L.marker([lat, lng], { icon: PIN_ICON, draggable: true }).addTo(map);
      marker.on('dragend', () => pickSpot(marker.getLatLng().lat, marker.getLatLng().lng));
    }
    marker.setLatLng([lat, lng]);
    status.textContent = `Pin at ${latInput.value}, ${lngInput.value}`;
  }

  // A spot picked on the map: pin it, then look up its address to fill the address box
  async function pickSpot(lat, lng) {
    placePin(lat, lng);
    const place = await askNominatim(`reverse?format=jsonv2&lat=${lat}&lon=${lng}`);
    if (place?.display_name) addressInput.value = place.display_name;
  }

  async function search() {
    const query = searchInput.value.trim();
    if (!query) return;
    status.textContent = 'Searching…';
    const results = await askNominatim(`search?format=jsonv2&limit=1&countrycodes=ph&q=${encodeURIComponent(query)}`);
    if (!results?.length) {
      status.textContent = 'No place found. Try a different name, or click the map.';
      return;
    }
    placePin(results[0].lat, results[0].lon);
    addressInput.value = results[0].display_name;
    map.setView([results[0].lat, results[0].lon], 16);
  }

  function useCurrentLocation() {
    if (!navigator.geolocation) {
      status.textContent = 'Your browser cannot share its location. Click the map instead.';
      return;
    }
    status.textContent = 'Finding your location…';
    navigator.geolocation.getCurrentPosition(
      (position) => {
        pickSpot(position.coords.latitude, position.coords.longitude);
        map.setView([position.coords.latitude, position.coords.longitude], 16);
      },
      () => { status.textContent = 'Location access was blocked. Search or click the map instead.'; },
    );
  }

  function clearPin() {
    latInput.value = '';
    lngInput.value = '';
    if (marker) marker.remove();
    marker = null;
    status.textContent = 'No location marked yet. Click the map to drop a pin.';
  }

  map.on('click', (event) => pickSpot(event.latlng.lat, event.latlng.lng));
  picker.querySelector('[data-map-search-button]').addEventListener('click', search);
  picker.querySelector('[data-map-locate]').addEventListener('click', useCurrentLocation);
  picker.querySelector('[data-map-clear]').addEventListener('click', clearPin);
  // Enter in the search box searches instead of saving the whole form
  searchInput.addEventListener('keydown', (event) => {
    if (event.key === 'Enter') {
      event.preventDefault();
      search();
    }
  });

  // Start at the saved pin, or show the whole country
  if (latInput.value && lngInput.value) {
    placePin(latInput.value, lngInput.value);
    map.setView([latInput.value, lngInput.value], 16);
  } else {
    map.setView(PHILIPPINES, 5);
  }
}

// Ask OpenStreetMap's free address service; returns null if it fails
async function askNominatim(path) {
  try {
    // Nominatim, like the map tiles, needs to know which site is asking (see the tile layer above)
    const response = await fetch(`${NOMINATIM}/${path}`, {
      headers: { 'Accept-Language': 'en' },
      referrerPolicy: 'strict-origin-when-cross-origin',
    });
    return response.ok ? await response.json() : null;
  } catch (error) {
    return null;
  }
}

document.querySelectorAll('[data-location-picker]').forEach(setUpPicker);
