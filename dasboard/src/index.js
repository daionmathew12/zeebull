import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./index.css";

// --- GLOBAL TIMEZONE OVERRIDE ---
// Forces all .toLocaleDateString, .toLocaleTimeString, and .toLocaleString
// to respect the system timezone fetched from settings, rather than falling back
// to the end user's browser (local device) timezone.
const getSystemTimezone = () => localStorage.getItem("SYSTEM_TIMEZONE") || "Asia/Kolkata";

const originalToLocaleString = Date.prototype.toLocaleString;
Date.prototype.toLocaleString = function (locales, options) {
  const opt = options || {};
  if (!opt.timeZone) {
    opt.timeZone = getSystemTimezone();
  }
  return originalToLocaleString.call(this, locales || "en-IN", opt);
};

const originalToLocaleDateString = Date.prototype.toLocaleDateString;
Date.prototype.toLocaleDateString = function (locales, options) {
  const opt = options || {};
  if (!opt.timeZone) {
    opt.timeZone = getSystemTimezone();
  }
  return originalToLocaleDateString.call(this, locales || "en-IN", opt);
};

const originalToLocaleTimeString = Date.prototype.toLocaleTimeString;
Date.prototype.toLocaleTimeString = function (locales, options) {
  const opt = options || {};
  if (!opt.timeZone) {
    opt.timeZone = getSystemTimezone();
  }
  return originalToLocaleTimeString.call(this, locales || "en-IN", opt);
};
// --------------------------------

// Make date inputs clickable anywhere to open calendar
const makeDateInputsClickable = () => {
  const handleDateInputClick = (e) => {
    const input = e.target;
    if (input && input.type === 'date') {
      // Use modern showPicker API if available (Chrome/Edge 99+, Safari 16.4+)
      if (typeof input.showPicker === 'function') {
        // Always open the picker when clicking anywhere on the date input
        // Small delay to ensure the input is focused first
        setTimeout(() => {
          try {
            const pickerResult = input.showPicker();
            // Only call .catch() if showPicker returns a promise
            if (pickerResult && typeof pickerResult.catch === 'function') {
              pickerResult.catch(() => {
                // showPicker may fail in some contexts (e.g., user interaction required)
                // Allow normal browser behavior in those cases
              });
            }
          } catch (err) {
            // showPicker may throw an error in some contexts
            // Allow normal browser behavior in those cases
            console.debug('showPicker failed:', err);
          }
        }, 50);
      }
    }
  };

  // Attach click handlers to all date inputs
  const attachHandlersBetter = () => {
    document.querySelectorAll('input[type="date"]').forEach(input => {
      // Check if handler is already attached
      if (!input.hasAttribute('data-date-clickable')) {
        input.setAttribute('data-date-clickable', 'true');
        input.addEventListener('click', handleDateInputClick);
      }
    });
  };

  // Initial attachment
  attachHandlersBetter();

  // Use MutationObserver to handle dynamically added date inputs
  const observer = new MutationObserver(attachHandlersBetter);
  observer.observe(document.body, {
    childList: true,
    subtree: true
  });
};

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', makeDateInputsClickable);
} else {
  makeDateInputsClickable();
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<App />);
