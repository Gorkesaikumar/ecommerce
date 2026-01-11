// Global Loading Manager
(function() {
    // Safety timeout: Remove skeleton after 3 seconds even if load event doesn't fire (failsafe)
    const SAFETY_TIMEOUT = 3000;
    
    // Function to hide skeleton
    function hideSkeleton() {
        const skeleton = document.getElementById('initial-skeleton-overlay');
        if (skeleton && !skeleton.classList.contains('hidden')) {
            skeleton.classList.add('hidden');
            
            // Remove from DOM after transition to free up memory
            setTimeout(() => {
                if (skeleton.parentNode) {
                    skeleton.parentNode.removeChild(skeleton);
                }
            }, 600); // 0.5s transition + buffer
        }
    }

    // Listener for window load (all assets loaded)
    window.addEventListener('load', hideSkeleton);

    // Failsafe backup
    setTimeout(hideSkeleton, SAFETY_TIMEOUT);

    // Also listen for a custom event 'app-ready' if we ever want to trigger manually from other scripts
    window.addEventListener('app-ready', hideSkeleton);
})();
