document.addEventListener('DOMContentLoaded', function() {
    // Add version badge under sidebar brand text
    var brandText = document.querySelector('.sidebar-brand-text');
    if (brandText) {
        var version = document.querySelector('meta[name="version"]');
        var versionStr = version ? version.getAttribute('content') : null;
        if (!versionStr) {
            var match = document.body.innerHTML.match(/release\s*=\s*["']([^"']+)["']/);
            if (!match) {
                var el = document.querySelector('[data-version]');
                versionStr = el ? el.getAttribute('data-version') : null;
            }
        }
        // Fallback: extract from the page metadata
        if (!versionStr) {
            var metaTags = document.querySelectorAll('meta');
            metaTags.forEach(function(m) {
                if (m.getAttribute('name') === 'generator') {
                    // not useful, skip
                }
            });
        }
        // Use the version from conf.py injected into the template
        var badge = document.createElement('span');
        badge.className = 'sidebar-version-badge';
        badge.textContent = 'v' + (document.querySelector('.footer-item a[href*="pypi"]') ? '' : DOCUMENTATION_OPTIONS.VERSION || '');
        if (typeof DOCUMENTATION_OPTIONS !== 'undefined' && DOCUMENTATION_OPTIONS.VERSION) {
            badge.textContent = 'v' + DOCUMENTATION_OPTIONS.VERSION;
            brandText.parentNode.insertBefore(badge, brandText.nextSibling);
        }
    }

    // Hide class prefix from method names in sidebar
    var methodLinks = document.querySelectorAll('li.toctree-l4 a code span.pre');
    methodLinks.forEach(function(span) {
        var fullText = span.textContent;
        var match = fullText.match(/\.([^.()]+\(\))/);
        if (match) {
            span.textContent = match[1];
        }
    });
});
