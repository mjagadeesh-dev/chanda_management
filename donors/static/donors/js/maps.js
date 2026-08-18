/**
 * Google Maps Geolocation & Reverse Geocoding Integration
 * SBVM Vinayaka Association - Chanda Collection Manager
 */

document.addEventListener('DOMContentLoaded', () => {
    const locateBtn = document.getElementById('locate-btn');
    const addressInput = document.getElementById('search-address-input');
    const latInput = document.getElementById('id_latitude');
    const lngInput = document.getElementById('id_longitude');
    const placeIdInput = document.getElementById('id_google_place_id');

    if (locateBtn) {
        locateBtn.addEventListener('click', () => {
            if (!navigator.geolocation) {
                alert("Geolocation is not supported by your browser/device.");
                return;
            }

            // Disable button and show locating status
            locateBtn.disabled = true;
            const originalContent = locateBtn.innerHTML;
            locateBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Locating...';
            
            if (addressInput) {
                addressInput.value = 'Fetching exact location, please wait...';
            }

            // Get GPS coordinates of the device
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    const lat = position.coords.latitude;
                    const lng = position.coords.longitude;

                    // Set coordinates input fields
                    if (latInput) latInput.value = lat.toFixed(6);
                    if (lngInput) lngInput.value = lng.toFixed(6);

                    console.log("GPS Coordinates Captured:", lat, lng);

                    // Perform Reverse Geocoding via Google Maps API
                    if (typeof google !== 'undefined' && google.maps && google.maps.Geocoder) {
                        const geocoder = new google.maps.Geocoder();
                        const latlng = { lat: lat, lng: lng };

                        geocoder.geocode({ location: latlng }, (results, status) => {
                            // Reset button state
                            locateBtn.disabled = false;
                            locateBtn.innerHTML = originalContent;

                            if (status === 'OK') {
                                if (results[0]) {
                                    // Populate address and Place ID
                                    if (addressInput) addressInput.value = results[0].formatted_address;
                                    if (placeIdInput) placeIdInput.value = results[0].place_id || '';
                                    
                                    console.log("Reverse Geocoding Success:", {
                                        address: results[0].formatted_address,
                                        place_id: results[0].place_id
                                    });
                                } else {
                                    if (addressInput) addressInput.value = `${lat.toFixed(6)}, ${lng.toFixed(6)}`;
                                    alert("Location captured, but no formatted address was found by the Google geocoder.");
                                }
                            } else {
                                if (addressInput) addressInput.value = `${lat.toFixed(6)}, ${lng.toFixed(6)}`;
                                console.error("Google Geocoder failed due to: " + status);
                                alert("GPS coordinates captured. However, address geocoding failed (Status: " + status + ").");
                            }
                        });
                    } else {
                        // If Google script fails to load, fallback to plain coordinates in address box
                        locateBtn.disabled = false;
                        locateBtn.innerHTML = originalContent;
                        if (addressInput) addressInput.value = `${lat.toFixed(6)}, ${lng.toFixed(6)}`;
                        alert("GPS coordinates captured. (Google Maps API failed to load for address translation).");
                    }
                },
                (error) => {
                    locateBtn.disabled = false;
                    locateBtn.innerHTML = originalContent;
                    if (addressInput) addressInput.value = '';
                    
                    let errorMsg = "Unable to retrieve your location.";
                    if (error.code === error.PERMISSION_DENIED) {
                        errorMsg = "Location permission denied. Please allow location access in your browser settings.";
                    } else if (error.code === error.POSITION_UNAVAILABLE) {
                        errorMsg = "Location information is unavailable (e.g., GPS is disabled).";
                    } else if (error.code === error.TIMEOUT) {
                        errorMsg = "The request to get device location timed out.";
                    }
                    alert(errorMsg);
                    console.error("Geolocation Error:", error);
                },
                {
                    enableHighAccuracy: true, // Request precise GPS coordinates
                    timeout: 10000,
                    maximumAge: 0
                }
            );
        });
    }
});

// Dummy callback for Google Maps API script load
window.initAutocomplete = function() {
    console.log("Google Maps API loaded successfully.");
};
