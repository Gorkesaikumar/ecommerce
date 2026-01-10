document.addEventListener('DOMContentLoaded', () => {
    
    // --- CSRF Handling ---
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    const csrftoken = getCookie('csrftoken');

    // --- Search Toggle ---
    // --- Search Toggle ---
    const searchTrigger = document.querySelector('.search-trigger');
    const searchOverlay = document.getElementById('searchOverlay');
    const closeSearchBtn = document.getElementById('closeSearchBtn');

    if(searchTrigger && searchOverlay) {
        function closeSearch() {
            searchOverlay.style.display = 'none';
        }

        searchTrigger.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            const isVisible = searchOverlay.style.display === 'block';
            
            // Close menu if open
            if(window.menuDropdown) window.menuDropdown.style.display = 'none'; // Assuming globally accessible or select again
            const menuDropdown = document.getElementById('menuDropdown');
            if(menuDropdown) menuDropdown.style.display = 'none';

            searchOverlay.style.display = isVisible ? 'none' : 'block';
            if(!isVisible) {
                const input = searchOverlay.querySelector('input');
                if(input) input.focus();
            }
        });
        
        if(closeSearchBtn) {
            closeSearchBtn.addEventListener('click', (e) => {
                 e.preventDefault(); 
                 e.stopPropagation();
                 closeSearch();
            });
        }
        
        // Close on click outside (modified to exclude search trigger)
        document.addEventListener('click', (e) => {
            if(!searchTrigger.contains(e.target) && !searchOverlay.contains(e.target)) {
                closeSearch();
            }
        });
    }

    // --- Add to Cart Logic ---
    const addToCartBtns = document.querySelectorAll('.btn-add-mini, .btn-add-large');
    const cartCountEl = document.querySelector('.cart-count');

    addToCartBtns.forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.preventDefault();
            e.stopPropagation();
            const productId = btn.getAttribute('data-product-id');
            
            if(!productId) {
                 if(window.showToast) window.showToast('This is a demo product. Please view real products.', true);
                 else alert('Demo product');
                 return;
            }

            const originalText = btn.innerHTML;
            btn.innerHTML = '...';
            btn.disabled = true;

            try {
                const response = await fetch('/api/v1/cart/items', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrftoken,
                    },
                    body: JSON.stringify({
                        product_id: productId,
                        quantity: 1,
                        length: 0, breadth: 0, height: 0
                    })
                });

                if (response.ok) {
                    btn.innerHTML = '✓';
                    btn.style.background = '#4CAF50';
                    btn.style.color = 'white';
                    
                    if(cartCountEl) {
                         let current = parseInt(cartCountEl.textContent) || 0;
                         cartCountEl.textContent = current + 1;
                    }
                    
                    if(window.showToast) window.showToast('Item added to cart');

                    setTimeout(() => {
                        btn.innerHTML = originalText;
                        btn.style.background = '';
                        btn.style.color = '';
                        btn.disabled = false;
                    }, 1500);
                } else {
                    const errorData = await response.json();
                    const msg = errorData.error || 'Could not add to cart';
                    if(window.showToast) window.showToast(msg, true);
                    else alert(msg);
                    
                    btn.innerHTML = originalText;
                    btn.disabled = false;
                }
            } catch (error) {
                console.error('Error adding to cart:', error);
                if(window.showToast) window.showToast('Network error', true);
                btn.innerHTML = originalText;
                btn.disabled = false;
            }
        });
    });

    // --- Checkout Logic ---
    const checkoutForm = document.getElementById('checkoutForm');
    if (checkoutForm) {
        checkoutForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const btn = checkoutForm.querySelector('button[type="submit"]');
            const errorDiv = document.getElementById('checkoutError');
            
            btn.disabled = true;
            btn.innerHTML = 'Processing...';
            errorDiv.style.display = 'none';

            const formData = new FormData(checkoutForm);
            const payload = {
                guest_email: formData.get('email'),
                guest_phone: formData.get('phone'),
                shipping_address: {
                    line1: formData.get('address'),
                    city: formData.get('city'),
                    zip_code: formData.get('zip'),
                    state: 'Telangana'
                }
            };

            try {
                const response = await fetch('/api/v1/orders/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrftoken,
                    },
                    body: JSON.stringify(payload)
                });

                if (response.ok) {
                    const order = await response.json();
                    window.location.href = `/checkout/success/?order_id=${order.id}`;
                } else {
                    const errorData = await response.json();
                    let msg = errorData.error || 'Checkout failed';
                    if(errorData.shipping_address) msg = 'Address: ' + JSON.stringify(errorData.shipping_address);
                    errorDiv.textContent = msg;
                    errorDiv.style.display = 'block';
                    btn.disabled = false;
                    btn.innerHTML = 'Place Order';
                }
            } catch (error) {
                console.error('Checkout error:', error);
                errorDiv.textContent = 'Network error. Please try again.';
                errorDiv.style.display = 'block';
                btn.disabled = false;
                btn.innerHTML = 'Place Order';
            }
        });
    }

    // --- Auth Logic: Send OTP ---
    const mobileForm = document.getElementById('mobileForm');
    if (mobileForm) {
        mobileForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const btn = mobileForm.querySelector('button[type="submit"]');
            const errorDiv = document.getElementById('loginError');
            const mobileInput = document.getElementById('mobileInput');
            
            const mobile = "+91" + mobileInput.value; // Assume +91 hardcoded for now or use select
            
            btn.disabled = true;
            btn.innerHTML = 'Sending...';
            errorDiv.style.display = 'none';

            try {
                const response = await fetch('/api/v1/auth/otp/send', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrftoken,
                    },
                    body: JSON.stringify({ mobile_number: mobile })
                });

                if (response.ok) {
                    // Success -> Redirect to verify
                    window.location.href = `/verify-otp/?mobile=${mobileInput.value}`;
                } else {
                    const errorData = await response.json();
                    errorDiv.textContent = errorData.error || 'Failed to send OTP';
                    errorDiv.style.display = 'block';
                    btn.disabled = false;
                    btn.innerHTML = 'Continue';
                }
            } catch (error) {
                errorDiv.textContent = 'Network error';
                errorDiv.style.display = 'block';
                btn.disabled = false;
                btn.innerHTML = 'Continue';
            }
        });
    }

    // --- Auth Logic: Verify OTP ---
    const otpForm = document.getElementById('otpForm');
    if (otpForm) {
        otpForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const btn = otpForm.querySelector('button[type="submit"]');
            const errorDiv = document.getElementById('otpError');
            const otpInput = document.getElementById('otpInput');
            const urlParams = new URLSearchParams(window.location.search);
            const mobile = "+91" + urlParams.get('mobile');

            if (!mobile) {
                errorDiv.textContent = "Mobile number missing";
                errorDiv.style.display = 'block';
                return;
            }

            btn.disabled = true;
            btn.innerHTML = 'Verifying...';
            errorDiv.style.display = 'none';

            try {
                const response = await fetch('/api/v1/auth/otp/verify', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrftoken,
                    },
                    body: JSON.stringify({ mobile_number: mobile, otp: otpInput.value })
                });

                if (response.ok) {
                    const data = await response.json();
                    // Login successful via Session (handled by backend)
                    // Redirect to dashboard or home
                    window.location.href = '/account/dashboard';
                } else {
                    const errorData = await response.json();
                    // Handle list or string errors
                    let msg = "Invalid OTP";
                    if (errorData.non_field_errors) msg = errorData.non_field_errors[0];
                    if (errorData.otp) msg = errorData.otp[0];
                    if (typeof errorData.error === 'string') msg = errorData.error;
                    
                    errorDiv.textContent = msg;
                    errorDiv.style.display = 'block';
                    btn.disabled = false;
                    btn.innerHTML = 'Verify & Login';
                }
            } catch (error) {
                errorDiv.textContent = 'Network error';
                errorDiv.style.display = 'block';
                btn.disabled = false;
                btn.innerHTML = 'Verify & Login';
            }
        });
    }

    // --- Mobile Menu ---
    // --- Menu Toggle (Dropdown) ---
    const menuBtn = document.querySelector('.menu-trigger');
    const menuDropdown = document.getElementById('menuDropdown');

    if(menuBtn && menuDropdown) {
        menuBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            const isVisible = menuDropdown.style.display === 'block';
            
            // Close other overlays
            if(searchOverlay) searchOverlay.style.display = 'none';
            
            menuDropdown.style.display = isVisible ? 'none' : 'block';
        });

        // Close on click outside
        document.addEventListener('click', (e) => {
            if(!menuBtn.contains(e.target) && !menuDropdown.contains(e.target)) {
                menuDropdown.style.display = 'none';
            }
        });
    }
});
