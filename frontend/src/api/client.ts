import axios from 'axios';

// 1. Resolve startup security token from URL or session storage
const urlParams = new URLSearchParams(window.location.search);
const queryToken = urlParams.get('token');

if (queryToken) {
  sessionStorage.setItem('baynuman_token', queryToken);
  // Clean up the URL to prevent token leakage in screen sharing / screenshots
  const newUrl = window.location.protocol + "//" + window.location.host + window.location.pathname;
  window.history.replaceState({ path: newUrl }, '', newUrl);
}

const token = sessionStorage.getItem('baynuman_token') || '';

export const API_BASE_URL = 'http://127.0.0.1:8765/api';
export const WS_BASE_URL = 'ws://127.0.0.1:8765/api';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
    'X-Baynuman-Token': token,
  },
});

export const updateApiToken = (newToken: string) => {
  sessionStorage.setItem('baynuman_token', newToken);
  apiClient.defaults.headers.common['X-Baynuman-Token'] = newToken;
};

export const getApiToken = (): string => {
  return sessionStorage.getItem('baynuman_token') || '';
};
