"""Control panel UI injected into the browser for recording control."""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.async_api import Page

    from testcaseer.recorder import Recorder


# JavaScript for the control panel UI
CONTROL_PANEL_JS = """
(function() {
    // Don't inject if already present
    if (document.getElementById('__testcaseer_panel__')) return;
    
    // Create panel container
    const panel = document.createElement('div');
    panel.id = '__testcaseer_panel__';
    
    // Inject styles
    const styles = document.createElement('style');
    styles.textContent = `
        #__testcaseer_panel__ {
            position: fixed;
            top: 10px;
            right: 10px;
            z-index: 2147483647;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            border: 2px solid #4ade80;
            border-radius: 12px;
            padding: 12px 16px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            font-size: 14px;
            color: #fff;
            box-shadow: 0 8px 32px rgba(0,0,0,0.4), 0 0 0 1px rgba(255,255,255,0.1);
            display: flex;
            align-items: center;
            gap: 12px;
            user-select: none;
            cursor: move;
            backdrop-filter: blur(8px);
        }
        
        #__testcaseer_panel__.recording {
            border-color: #ef4444;
            box-shadow: 0 8px 32px rgba(239, 68, 68, 0.3), 0 0 0 1px rgba(255,255,255,0.1);
        }
        
        #__testcaseer_panel__ .logo {
            font-weight: 700;
            font-size: 15px;
            color: #4ade80;
            letter-spacing: -0.5px;
        }
        
        #__testcaseer_panel__ .divider {
            width: 1px;
            height: 24px;
            background: rgba(255,255,255,0.2);
        }
        
        #__testcaseer_panel__ .status {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        #__testcaseer_panel__ .status-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: #666;
            transition: background 0.3s;
        }
        
        #__testcaseer_panel__ .status-dot.recording {
            background: #ef4444;
            animation: __tc_pulse 1.5s ease-in-out infinite;
        }
        
        @keyframes __tc_pulse {
            0%, 100% { opacity: 1; box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7); }
            50% { opacity: 0.8; box-shadow: 0 0 0 8px rgba(239, 68, 68, 0); }
        }
        
        #__testcaseer_panel__ .status-text {
            font-size: 13px;
            color: #a0a0a0;
        }
        
        #__testcaseer_panel__ .steps-count {
            font-size: 12px;
            color: #888;
            min-width: 60px;
        }
        
        #__testcaseer_panel__ button {
            background: #4ade80;
            color: #000;
            border: none;
            border-radius: 8px;
            padding: 8px 16px;
            font-weight: 600;
            font-size: 13px;
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        
        #__testcaseer_panel__ button:hover {
            background: #22c55e;
            transform: translateY(-1px);
        }
        
        #__testcaseer_panel__ button:active {
            transform: translateY(0);
        }
        
        #__testcaseer_panel__ button.stop {
            background: #ef4444;
            color: #fff;
        }
        
        #__testcaseer_panel__ button.stop:hover {
            background: #dc2626;
        }
        
        #__testcaseer_panel__ .message {
            font-size: 13px;
            color: #4ade80;
            font-weight: 500;
        }
    `;
    document.head.appendChild(styles);
    
    // Panel HTML
    panel.innerHTML = `
        <span class="logo">TestCaseer</span>
        <span class="divider"></span>
        <div class="status">
            <span class="status-dot" id="__tc_status_dot__"></span>
            <span class="status-text" id="__tc_status_text__">Ready</span>
        </div>
        <span class="steps-count" id="__tc_steps_count__"></span>
        <button id="__tc_start_btn__">▶ Start</button>
        <button id="__tc_stop_btn__" class="stop" style="display:none">⏹ Stop</button>
        <span class="message" id="__tc_message__" style="display:none"></span>
    `;
    
    document.body.appendChild(panel);
    
    // Make panel draggable
    let isDragging = false;
    let dragOffsetX = 0;
    let dragOffsetY = 0;
    
    panel.addEventListener('mousedown', (e) => {
        if (e.target.tagName === 'BUTTON') return;
        isDragging = true;
        dragOffsetX = e.clientX - panel.offsetLeft;
        dragOffsetY = e.clientY - panel.offsetTop;
        panel.style.cursor = 'grabbing';
    });
    
    document.addEventListener('mousemove', (e) => {
        if (!isDragging) return;
        panel.style.left = (e.clientX - dragOffsetX) + 'px';
        panel.style.top = (e.clientY - dragOffsetY) + 'px';
        panel.style.right = 'auto';
    });
    
    document.addEventListener('mouseup', () => {
        isDragging = false;
        panel.style.cursor = 'move';
    });
    
    // Button handlers
    document.getElementById('__tc_start_btn__').onclick = async () => {
        try {
            await window.__testcaseer_start_recording();
        } catch (e) {
            console.error('TestCaseer: Failed to start recording', e);
        }
    };
    
    document.getElementById('__tc_stop_btn__').onclick = async () => {
        try {
            await window.__testcaseer_stop_recording();
        } catch (e) {
            console.error('TestCaseer: Failed to stop recording', e);
        }
    };
})();
"""


def get_update_ui_script(is_recording: bool, steps_count: int, message: str = "") -> str:
    """
    Generate JavaScript to update the control panel UI.

    Args:
        is_recording: Whether recording is active
        steps_count: Number of recorded steps
        message: Optional message to display

    Returns:
        JavaScript code to execute
    """
    status_class = "recording" if is_recording else ""
    status_text = "Recording..." if is_recording else "Ready"
    start_display = "none" if is_recording else "inline-flex"
    stop_display = "inline-flex" if is_recording else "none"
    steps_text = f"{steps_count} steps" if steps_count > 0 else ""
    panel_class = "recording" if is_recording else ""
    message_display = "inline" if message else "none"

    return f"""
    (function() {{
        const panel = document.getElementById('__testcaseer_panel__');
        if (!panel) return;
        
        panel.className = '{panel_class}';
        
        const dot = document.getElementById('__tc_status_dot__');
        if (dot) dot.className = 'status-dot {status_class}';
        
        const text = document.getElementById('__tc_status_text__');
        if (text) text.textContent = '{status_text}';
        
        const startBtn = document.getElementById('__tc_start_btn__');
        if (startBtn) startBtn.style.display = '{start_display}';
        
        const stopBtn = document.getElementById('__tc_stop_btn__');
        if (stopBtn) stopBtn.style.display = '{stop_display}';
        
        const steps = document.getElementById('__tc_steps_count__');
        if (steps) steps.textContent = '{steps_text}';
        
        const msg = document.getElementById('__tc_message__');
        if (msg) {{
            msg.textContent = '{message}';
            msg.style.display = '{message_display}';
        }}
    }})();
    """


async def inject_control_panel(page: Page, recorder: Recorder) -> None:
    """
    Inject the control panel into the page.

    Args:
        page: Playwright Page object
        recorder: Recorder instance to bind controls to
    """
    # Expose Python functions to JavaScript
    await page.expose_function(
        "__testcaseer_start_recording",
        recorder.start_recording,
    )
    await page.expose_function(
        "__testcaseer_stop_recording",
        recorder.stop_recording,
    )

    # Add script that runs on every page load
    await page.add_init_script(CONTROL_PANEL_JS)

    # Also run it now for the current page
    await page.evaluate(CONTROL_PANEL_JS)


async def update_panel_ui(
    page: Page, is_recording: bool, steps_count: int, message: str = ""
) -> None:
    """
    Update the control panel UI state.

    Args:
        page: Playwright Page object
        is_recording: Whether recording is active
        steps_count: Number of recorded steps
        message: Optional message to display
    """
    script = get_update_ui_script(is_recording, steps_count, message)
    # Page might have navigated, panel will be re-injected
    with contextlib.suppress(Exception):
        await page.evaluate(script)

