/**
 * Date and Time Utilities for India/Kerala (IST - UTC+5:30)
 */

// IST timezone constant
const IST_TIMEZONE = 'Asia/Kolkata';

/**
 * Ensures a date string has a timezone indicator. 
 * If it's an ISO string missing one, appends 'Z' to treat as UTC.
 */
export const ensureUTC = (dateString) => {
  if (typeof dateString !== 'string') return dateString;
  if (!dateString.includes('T')) return dateString;
  
  // If it contains T but no Z and no + offset after the T
  if (!dateString.endsWith('Z') && !dateString.includes('+', dateString.indexOf('T'))) {
    return dateString + 'Z';
  }
  return dateString;
};

/**
 * Helper to ensure we have a valid Date object, treating naive ISO strings as UTC
 * @param {string|Date} dateSource - Input date
 * @returns {Date}
 */
const ensureDate = (dateSource) => {
  if (!dateSource) return null;
  if (dateSource instanceof Date) return dateSource;
  
  if (typeof dateSource === 'string') {
    // If it's an ISO-like string (has T) but lacks timezone info (Z or +/-05:30)
    // we append 'Z' so the browser treats it as UTC (standard for our backend naive datetimes)
    const hasT = dateSource.includes('T');
    const hasTZ = dateSource.includes('Z') || /[+-]\d{2}(:?\d{2})?$/.test(dateSource);
    
    if (hasT && !hasTZ) {
      return new Date(dateSource + 'Z');
    }
    return new Date(dateSource);
  }
  
  return new Date(dateSource);
};

/**
 * Format date in IST timezone
 * @param {string|Date} dateString - Date string or Date object
 * @param {object} options - Intl.DateTimeFormat options
 * @returns {string} Formatted date string
 */
export const formatDateIST = (dateString, options = {}) => {
  if (!dateString) return '-';
  
  const date = ensureDate(dateString);
  
  if (!date || isNaN(date.getTime())) return '-';
  
  const defaultOptions = {
    timeZone: IST_TIMEZONE,
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    ...options
  };
  
  return new Intl.DateTimeFormat('en-IN', defaultOptions).format(date);
};

/**
 * Format date and time in IST timezone
 * @param {string|Date} dateString - Date string or Date object
 * @param {object} options - Intl.DateTimeFormat options
 * @returns {string} Formatted date and time string
 */
export const formatDateTimeIST = (dateString, options = {}) => {
  if (!dateString) return '-';
  
  const date = ensureDate(dateString);
  
  if (!date || isNaN(date.getTime())) return '-';
  
  const defaultOptions = {
    timeZone: IST_TIMEZONE,
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: true,
    ...options
  };
  
  return new Intl.DateTimeFormat('en-IN', defaultOptions).format(date);
};

/**
 * Format time only in IST timezone
 * @param {string|Date} dateString - Date string or Date object
 * @returns {string} Formatted time string
 */
export const formatTimeIST = (dateString) => {
  if (!dateString) return '-';
  
  const date = ensureDate(dateString);
  
  if (!date || isNaN(date.getTime())) return '-';
  
  return new Intl.DateTimeFormat('en-IN', {
    timeZone: IST_TIMEZONE,
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: true
  }).format(date);
};

/**
 * Get current date in IST timezone (YYYY-MM-DD format for date inputs)
 * @returns {string} Current date in YYYY-MM-DD format
 */
export const getCurrentDateIST = () => {
  const now = new Date();
  const istDate = new Date(now.toLocaleString('en-US', { timeZone: IST_TIMEZONE }));
  
  const year = istDate.getFullYear();
  const month = String(istDate.getMonth() + 1).padStart(2, '0');
  const day = String(istDate.getDate()).padStart(2, '0');
  
  return `${year}-${month}-${day}`;
};

/**
 * Get current datetime in IST timezone (ISO format)
 * @returns {string} Current datetime in ISO format
 */
export const getCurrentDateTimeIST = () => {
  const now = new Date();
  const istDate = new Date(now.toLocaleString('en-US', { timeZone: IST_TIMEZONE }));
  return istDate.toISOString();
};

/**
 * Convert date to IST and return as ISO string
 * @param {string|Date} dateString - Date string or Date object
 * @returns {string} ISO string in IST
 */
export const toISTISO = (dateString) => {
  if (!dateString) return null;
  
  const date = ensureDate(dateString);
  
  if (!date || isNaN(date.getTime())) return null;
  
  // Get IST time
  const istString = date.toLocaleString('en-US', { timeZone: IST_TIMEZONE });
  const istDate = new Date(istString);
  
  return istDate.toISOString();
};

/**
 * Format date for display (short format: DD MMM YYYY)
 * @param {string|Date} dateString - Date string or Date object
 * @returns {string} Formatted date
 */
export const formatDateShort = (dateString) => {
  return formatDateIST(dateString, {
    day: '2-digit',
    month: 'short',
    year: 'numeric'
  });
};

/**
 * Format date for display (long format: DD MMMM YYYY)
 * @param {string|Date} dateString - Date string or Date object
 * @returns {string} Formatted date
 */
export const formatDateLong = (dateString) => {
  return formatDateIST(dateString, {
    day: '2-digit',
    month: 'long',
    year: 'numeric'
  });
};

/**
 * Format datetime for display (DD MMM YYYY, HH:MM AM/PM)
 * @param {string|Date} dateString - Date string or Date object
 * @returns {string} Formatted datetime
 */
export const formatDateTimeShort = (dateString) => {
  return formatDateTimeIST(dateString, {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: true
  });
};

/**
 * Format datetime for display (DD MMMM YYYY, HH:MM:SS AM/PM)
 * @param {string|Date} dateString - Date string or Date object
 * @returns {string} Formatted datetime
 */
export const formatDateTimeLong = (dateString) => {
  return formatDateTimeIST(dateString, {
    day: '2-digit',
    month: 'long',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: true
  });
};

/**
 * Get relative time (e.g., "2 hours ago", "yesterday")
 * @param {string|Date} dateString - Date string or Date object
 * @returns {string} Relative time string
 */
export const getRelativeTime = (dateString) => {
  if (!dateString) return '-';
  
  const date = ensureDate(dateString);
  
  if (!date || isNaN(date.getTime())) return '-';
  
  const now = new Date();
  const nowIST = new Date(now.toLocaleString('en-US', { timeZone: IST_TIMEZONE }));
  const dateIST = new Date(date.toLocaleString('en-US', { timeZone: IST_TIMEZONE }));
  
  const diffMs = nowIST - dateIST;
  const diffSecs = Math.floor(diffMs / 1000);
  const diffMins = Math.floor(diffSecs / 60);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);
  
  if (diffSecs < 60) return 'Just now';
  if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`;
  if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
  if (diffDays === 1) return 'Yesterday';
  if (diffDays < 7) return `${diffDays} days ago`;
  
  return formatDateShort(dateString);
};

export default {
  formatDateIST,
  formatDateTimeIST,
  formatTimeIST,
  getCurrentDateIST,
  getCurrentDateTimeIST,
  toISTISO,
  formatDateShort,
  formatDateLong,
  formatDateTimeShort,
  formatDateTimeLong,
  getRelativeTime,
  IST_TIMEZONE
};








