"""Browser event handling and DOM event injection for TestCaseer."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from playwright.async_api import Page

    from testcaseer.recorder import Recorder


# JavaScript for capturing DOM events
EVENT_LISTENER_JS = """
(function() {
    // Don't inject twice
    if (window.__testcaseer_events_injected) return;
    window.__testcaseer_events_injected = true;
    
    // Helper: Check if element is part of control panel
    function isControlPanel(el) {
        return el.closest('#__testcaseer_panel__') !== null;
    }
    
    // Helper: Generate CSS selector for element
    function getCssSelector(el) {
        if (!el || el === document.body || el === document.documentElement) {
            return 'body';
        }
        
        // Try ID first
        if (el.id) {
            return '#' + CSS.escape(el.id);
        }
        
        // Try data-testid
        if (el.dataset && el.dataset.testid) {
            return '[data-testid="' + el.dataset.testid + '"]';
        }
        
        // Try unique class combination
        if (el.className && typeof el.className === 'string') {
            const classes = el.className.trim().split(/\\s+/).filter(c => c.length > 0);
            if (classes.length > 0) {
                const selector = el.tagName.toLowerCase() + '.' + classes.join('.');
                if (document.querySelectorAll(selector).length === 1) {
                    return selector;
                }
            }
        }
        
        // Build path from parent
        const parent = el.parentElement;
        if (!parent) {
            return el.tagName.toLowerCase();
        }
        
        const siblings = Array.from(parent.children).filter(
            child => child.tagName === el.tagName
        );
        
        if (siblings.length === 1) {
            return getCssSelector(parent) + ' > ' + el.tagName.toLowerCase();
        }
        
        const index = siblings.indexOf(el) + 1;
        return getCssSelector(parent) + ' > ' + el.tagName.toLowerCase() + ':nth-of-type(' + index + ')';
    }
    
    // Helper: Get XPath for element
    function getXPath(el) {
        if (!el) return '';
        if (el.id) return '//*[@id="' + el.id + '"]';
        if (el === document.body) return '/html/body';
        
        const siblings = el.parentNode ? Array.from(el.parentNode.children) : [];
        const sameTagSiblings = siblings.filter(s => s.tagName === el.tagName);
        
        let path = '/' + el.tagName.toLowerCase();
        if (sameTagSiblings.length > 1) {
            path += '[' + (sameTagSiblings.indexOf(el) + 1) + ']';
        }
        
        if (el.parentNode && el.parentNode !== document) {
            return getXPath(el.parentNode) + path;
        }
        return path;
    }
    
    // Helper: Get element info
    function getElementInfo(el) {
        const rect = el.getBoundingClientRect();
        return {
            selector: getCssSelector(el),
            xpath: getXPath(el),
            tagName: el.tagName.toLowerCase(),
            text: (el.innerText || el.textContent || '').substring(0, 100).trim(),
            placeholder: el.placeholder || null,
            id: el.id || null,
            name: el.name || null,
            type: el.type || null,
            href: el.href || null,
            value: el.value || null,
            className: el.className || null,
            attributes: {},
            boundingBox: {
                x: rect.x,
                y: rect.y,
                width: rect.width,
                height: rect.height
            }
        };
    }
    
    // Track input values for debouncing
    let inputDebounceTimer = null;
    let lastInputValue = {};
    
    // Click handler
    document.addEventListener('click', async (e) => {
        if (isControlPanel(e.target)) return;
        
        const info = getElementInfo(e.target);
        info.eventType = 'click';
        info.clientX = e.clientX;
        info.clientY = e.clientY;
        
        try {
            await window.__testcaseer_on_action(info);
        } catch (err) {
            console.debug('TestCaseer: click handler error', err);
        }
    }, true);
    
    // Double-click handler
    document.addEventListener('dblclick', async (e) => {
        if (isControlPanel(e.target)) return;
        
        const info = getElementInfo(e.target);
        info.eventType = 'dblclick';
        
        try {
            await window.__testcaseer_on_action(info);
        } catch (err) {
            console.debug('TestCaseer: dblclick handler error', err);
        }
    }, true);
    
    // Input handler (debounced)
    document.addEventListener('input', (e) => {
        if (isControlPanel(e.target)) return;
        
        const el = e.target;
        const selector = getCssSelector(el);
        
        // Clear previous timer
        if (inputDebounceTimer) {
            clearTimeout(inputDebounceTimer);
        }
        
        // Store current value
        lastInputValue[selector] = el.value;
        
        // Debounce: wait 500ms after last keystroke
        inputDebounceTimer = setTimeout(async () => {
            const info = getElementInfo(el);
            info.eventType = 'input';
            info.value = lastInputValue[selector];
            
            try {
                await window.__testcaseer_on_action(info);
            } catch (err) {
                console.debug('TestCaseer: input handler error', err);
            }
            
            delete lastInputValue[selector];
        }, 500);
    }, true);
    
    // Change handler (for select, checkbox, radio)
    document.addEventListener('change', async (e) => {
        if (isControlPanel(e.target)) return;
        
        const el = e.target;
        const info = getElementInfo(el);
        
        // Determine action type based on element
        if (el.type === 'checkbox') {
            info.eventType = el.checked ? 'check' : 'uncheck';
            info.checked = el.checked;
        } else if (el.type === 'radio') {
            info.eventType = 'check';
            info.checked = el.checked;
        } else if (el.tagName.toLowerCase() === 'select') {
            info.eventType = 'select';
            info.value = el.value;
            info.selectedText = el.options[el.selectedIndex]?.text || '';
        } else {
            // Skip for regular inputs (handled by input event)
            return;
        }
        
        try {
            await window.__testcaseer_on_action(info);
        } catch (err) {
            console.debug('TestCaseer: change handler error', err);
        }
    }, true);
    
    // Keypress handler (for special keys like Enter)
    document.addEventListener('keydown', async (e) => {
        if (isControlPanel(e.target)) return;
        
        // Only capture special keys
        const specialKeys = ['Enter', 'Escape', 'Tab'];
        if (!specialKeys.includes(e.key)) return;
        
        const info = getElementInfo(e.target);
        info.eventType = 'keypress';
        info.key = e.key;
        
        try {
            await window.__testcaseer_on_action(info);
        } catch (err) {
            console.debug('TestCaseer: keydown handler error', err);
        }
    }, true);
    
    console.log('TestCaseer: Event listeners injected');
})();
"""


async def setup_event_listeners(page: Page, recorder: Recorder) -> None:
    """
    Set up DOM event listeners on the page.

    Injects JavaScript that captures user interactions and sends them
    to the Python recorder via exposed functions.

    Args:
        page: Playwright Page object
        recorder: Recorder instance to receive events
    """
    # Expose the action handler to JavaScript
    await page.expose_function(
        "__testcaseer_on_action",
        recorder.on_action,
    )

    # Add script that runs on every page load
    await page.add_init_script(EVENT_LISTENER_JS)

    # Also run it now for the current page
    await page.evaluate(EVENT_LISTENER_JS)


async def reinject_listeners(page: Page) -> None:
    """
    Re-inject event listeners after navigation.

    Called when page navigates to ensure listeners are present.

    Args:
        page: Playwright Page object
    """
    try:
        await page.evaluate(EVENT_LISTENER_JS)
    except Exception:
        # Page might still be loading
        pass


def parse_element_info(data: dict[str, Any]) -> dict[str, Any]:
    """
    Parse element info from JavaScript into Python-friendly format.

    Args:
        data: Raw element info from JavaScript

    Returns:
        Cleaned element info dictionary
    """
    return {
        "selector": data.get("selector", ""),
        "xpath": data.get("xpath"),
        "tag_name": data.get("tagName", ""),
        "text": data.get("text"),
        "placeholder": data.get("placeholder"),
        "attributes": {
            k: v
            for k, v in {
                "id": data.get("id"),
                "name": data.get("name"),
                "type": data.get("type"),
                "href": data.get("href"),
                "class": data.get("className"),
            }.items()
            if v
        },
        "bounding_box": data.get("boundingBox", {}),
    }

