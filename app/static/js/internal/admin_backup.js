// admin_backup.js

// Tab Switching Logic
function switchTab(tabId) {
    // Hide all tab contents
    document.querySelectorAll('.tab-content').forEach(el => {
        el.classList.add('hidden');
        el.classList.remove('block');
    });
    
    // Reset all tab buttons
    document.querySelectorAll('.tab-btn').forEach(el => {
        // Remove active styles
        el.classList.remove('text-blue-600', 'bg-blue-50');
        // Add inactive styles
        el.classList.add('text-slate-500', 'hover:text-slate-700', 'hover:bg-slate-50');
        
        // Hide indicator
        const indicator = el.querySelector('.tab-indicator');
        if (indicator) {
            indicator.classList.add('hidden');
        }
    });
    
    // Show selected tab content
    const selectedContent = document.getElementById(tabId);
    if (selectedContent) {
        selectedContent.classList.remove('hidden');
        selectedContent.classList.add('block');
    }
    
    // Activate selected tab button
    const activeBtn = document.getElementById('btn-' + tabId);
    if (activeBtn) {
        // Remove inactive styles
        activeBtn.classList.remove('text-slate-500', 'hover:text-slate-700', 'hover:bg-slate-50');
        // Add active styles
        activeBtn.classList.add('text-blue-600', 'bg-blue-50');
        
        // Show indicator
        const indicator = activeBtn.querySelector('.tab-indicator');
        if (indicator) {
            indicator.classList.remove('hidden');
        }
    }
}
