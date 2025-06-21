// Add this at the top for Node.js EventSource support
if (typeof EventSource === 'undefined') {
  try {
    const eventsourceModule = require('eventsource');
    global.EventSource = eventsourceModule.EventSource || eventsourceModule;
  } catch (error) {
    console.warn('EventSource polyfill not found. Install with: npm install eventsource');
  }
}

/**
 * Rocket Alert Live API Client
 * Simple JavaScript implementation for accessing Israeli rocket alert data
 * API Base: https://agg.rocketalert.live/api
 */

class RocketAlertAPI {
  constructor() {
    this.BASE_URL = 'https://agg.rocketalert.live/api';
    this.V1_URL = `${this.BASE_URL}/v1`;
    this.V2_URL = `${this.BASE_URL}/v2`;

    // Alert type constants
    this.ALERT_TYPES = {
      ALL: 0,
      ROCKETS: 1,
      UAV: 6, // Unmanned Aerial Vehicle (drone)
      KEEP_ALIVE: 'KEEP_ALIVE'
    };

    this.MAX_RECENT_ALERTS = 30;
  }

  /**
   * Helper function to make HTTP requests
   */
  async makeRequest(url, params = {}) {
    try {
      const queryString = new URLSearchParams(params).toString();
      const fullUrl = queryString ? `${url}?${queryString}` : url;

      // Add browser headers to mimic a real browser request
      const headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-US,en;q=0.9,he;q=0.8,he-IL;q=0.7',
        'Cache-Control': 'max-age=0',
        'Sec-Ch-Ua': '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36'
      };

      const response = await fetch(fullUrl, { headers });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      // Check if API returned an error
      if (data.success === false) {
        console.warn(`API returned error for ${url}:`, data.incidentId || 'Unknown error');
        console.warn('This might be a temporary server issue or rate limiting');
      }

      return data;
    } catch (error) {
      console.error('API Request failed:', error);
      throw error;
    }
  }

  /**
   * Format date to ISO string for API
   */
  formatDate(date) {
    return new Date(date).toISOString();
  }

  /**
   * Filter only rocket and UAV alerts
   */
  filterRocketAndUAVAlerts(response) {
    if (response.payload && Array.isArray(response.payload)) {
      response.payload.forEach(dateEntry => {
        if (dateEntry.alerts) {
          dateEntry.alerts = dateEntry.alerts.filter(alert =>
            alert.alertTypeId === this.ALERT_TYPES.ROCKETS ||
            alert.alertTypeId === this.ALERT_TYPES.UAV
          );
        }
      });
    }
    return response;
  }

  /**
   * Get detailed alert data for alerts in the given date range
   * @param {string|Date} from - From date (optional, API may reject date params)
   * @param {string|Date} to - To date (optional, API may reject date params) 
   * @param {number} alertTypeId - Alert type filter (default: all)
   */
  async getDetailedAlerts(from = null, to = null, alertTypeId = this.ALERT_TYPES.ALL) {
    // Try without date parameters first, as API seems to reject them
    try {
      const params = alertTypeId !== this.ALERT_TYPES.ALL ? { alertTypeId } : {};
      const response = await this.makeRequest(`${this.V1_URL}/alerts/details`, params);
      return this.filterRocketAndUAVAlerts(response);
    } catch (error) {
      console.warn('Failed to get detailed alerts:', error.message);
      throw error;
    }
  }

  /**
   * Get the most recent alerts in the given time range
   * @param {string|Date} from - From date
   * @param {string|Date} to - To date
   */
  async getMostRecentAlerts(from, to) {
    try {
      const response = await this.getDetailedAlerts(from, to);

      if (!response.success || response.payload.length === 0) {
        return [];
      }

      // Combine alerts from multiple days if needed
      const alerts = response.payload.length > 1
        ? response.payload[0].alerts.concat(response.payload[1].alerts)
        : response.payload[0].alerts;

      // Return the most recent alerts (limited by MAX_RECENT_ALERTS)
      return alerts.slice(-this.MAX_RECENT_ALERTS);
    } catch (error) {
      console.error('Error getting most recent alerts:', error);
      return [];
    }
  }

  /**
   * Get total alert count by day for the given date range
   * @param {string|Date} from - From date (optional, API may reject date params)
   * @param {string|Date} to - To date (optional, API may reject date params)
   * @param {number} alertTypeId - Alert type filter
   */
  async getTotalAlertsByDay(from = null, to = null, alertTypeId = this.ALERT_TYPES.ALL) {
    // Try without date parameters first, as API seems to reject them
    try {
      const params = alertTypeId !== this.ALERT_TYPES.ALL ? { alertTypeId } : {};
      return await this.makeRequest(`${this.V1_URL}/alerts/daily`, params);
    } catch (error) {
      console.warn('Failed to get daily alerts:', error.message);
      throw error;
    }
  }

  /**
   * Get total alert count for the given date range
   * @param {string|Date} from - From date (optional, API may reject date params)
   * @param {string|Date} to - To date (optional, API may reject date params)
   * @param {number} alertTypeId - Alert type filter
   */
  async getTotalAlerts(from = null, to = null, alertTypeId = this.ALERT_TYPES.ALL) {
    // Try without date parameters first, as API seems to reject them
    try {
      const params = alertTypeId !== this.ALERT_TYPES.ALL ? { alertTypeId } : {};
      return await this.makeRequest(`${this.V1_URL}/alerts/total`, params);
    } catch (error) {
      console.warn('Failed to get total alerts:', error.message);
      throw error;
    }
  }

  /**
   * Get the date and location of the most recent alert
   */
  async getMostRecentAlert() {
    return await this.makeRequest(`${this.V1_URL}/alerts/latest`);
  }

  /**
   * Get the top N most targeted locations
   * @param {string|Date} from - From date (optional, API may reject date params)
   * @param {string|Date} to - To date (optional, API may reject date params)
   * @param {number} limit - Number of locations (default: 10)
   */
  async getMostTargetedLocations(from = null, to = null, limit = 10) {
    // Try without date parameters first, as API seems to reject them
    try {
      const params = limit !== 10 ? { limit } : {};
      return await this.makeRequest(`${this.V1_URL}/alerts/top/place`, params);
    } catch (error) {
      console.warn('Failed to get most targeted locations:', error.message);
      throw error;
    }
  }

  /**
   * Get the top N most targeted regions
   * @param {string|Date} from - From date (optional, API may reject date params)
   * @param {string|Date} to - To date (optional, API may reject date params)
   * @param {number} limit - Number of regions (default: 10)
   */
  async getMostTargetedRegions(from = null, to = null, limit = 10) {
    // Try without date parameters first, as API seems to reject them
    try {
      const params = limit !== 10 ? { limit } : {};
      return await this.makeRequest(`${this.V1_URL}/alerts/top/area`, params);
    } catch (error) {
      console.warn('Failed to get most targeted regions:', error.message);
      throw error;
    }
  }

  /**
   * Get real-time alerts from cache (V2 API)
   */
  async getRealTimeAlertCache() {
    try {
      const response = await this.makeRequest(`${this.V2_URL}/alerts/real-time/cached`);

      if (!response.success) {
        return { alerts: [], count: 0 };
      }

      const payload = {
        alerts: [],
        count: response.payload.length
      };

      // Flatten all alerts from all items
      const allAlerts = [];
      response.payload.forEach(item => {
        if (item.alerts) {
          allAlerts.push(...item.alerts);
        }
      });

      // Remove duplicate alerts based on location name
      const seenLocations = new Set();
      allAlerts.forEach(alert => {
        if (!seenLocations.has(alert.englishName)) {
          seenLocations.add(alert.englishName);
          payload.alerts.push(alert);
        }
      });

      payload.count = payload.alerts.length;
      return payload;
    } catch (error) {
      console.error('Error getting real-time alert cache:', error);
      return { alerts: [], count: 0 };
    }
  }

  /**
   * Create EventSource for real-time alerts
   * @param {function} onAlert - Callback function for new alerts
   * @param {function} onError - Callback function for errors
   */
  createRealTimeConnection(onAlert, onError) {
    let EventSourceConstructor = EventSource;

    // Handle Node.js environment
    if (typeof EventSource === 'undefined' || !EventSource) {
      try {
        const eventsourceModule = require('eventsource');
        EventSourceConstructor = eventsourceModule.EventSource || eventsourceModule;
      } catch (error) {
        console.warn('EventSource not available. Install with: npm install eventsource');
        if (onError) {
          onError(new Error('EventSource not available'));
        }
        return null;
      }
    }

    const eventSource = new EventSourceConstructor(`${this.V2_URL}/alerts/real-time`);

    eventSource.onopen = () => {
      console.log('Real-time connection opened');
    };

    eventSource.addEventListener('message', (event) => {
      try {
        const data = JSON.parse(event.data);

        // Skip keep-alive messages
        if (data.alerts && data.alerts[0] && data.alerts[0].name === this.ALERT_TYPES.KEEP_ALIVE) {
          return;
        }

        // Filter only rocket and UAV alerts
        const filteredAlerts = data.alerts.filter(alert =>
          alert.alertTypeId === this.ALERT_TYPES.ROCKETS ||
          alert.alertTypeId === this.ALERT_TYPES.UAV
        );

        if (filteredAlerts.length > 0 && onAlert) {
          onAlert(filteredAlerts);
        }
      } catch (error) {
        console.error('Error parsing real-time alert:', error);
      }
    });

    eventSource.onerror = (error) => {
      console.error('EventSource error:', error);
      if (onError) {
        onError(error);
      }
    };

    return eventSource;
  }

  /**
   * Helper function to get date 24 hours ago
   */
  get24HoursAgo() {
    const date = new Date();
    date.setHours(date.getHours() - 24);
    return date;
  }

  /**
   * Helper function to get current date
   */
  getNow() {
    return new Date();
  }
}

// Usage Examples:
async function examples() {
  const api = new RocketAlertAPI();

  try {
    console.log('=== Testing Rocket Alert API ===\n');

    // Get most recent alert
    // console.log('1. Most recent alert:');
    // const mostRecent = await api.getMostRecentAlert();
    // console.log(JSON.stringify(mostRecent, null, 2));
    // console.log();



    // // Get alerts from last 24 hours
    // console.log('2. Alerts from last 24 hours:');
    // const recentAlerts = await api.getMostRecentAlerts(api.get24HoursAgo(), api.getNow());
    // console.log(`Found ${recentAlerts.length} recent alerts`);
    // if (recentAlerts.length > 0) {
    //   console.log('First alert:', JSON.stringify(recentAlerts[0], null, 2));
    // }
    // console.log();




    
    // // Get daily statistics for last 7 days (more reasonable range)
    // console.log('3. Daily statistics for last 7 days:');
    // const weekAgo = new Date();
    // weekAgo.setDate(weekAgo.getDate() - 7);
    // const dailyStats = await api.getTotalAlertsByDay(weekAgo, api.getNow());
    // console.log(JSON.stringify(dailyStats, null, 2));
    // console.log();

    // // Get total alerts for a shorter period
    // console.log('4. Total alerts for last 7 days:');
    // const totalAlerts = await api.getTotalAlerts(weekAgo, api.getNow());
    // console.log(JSON.stringify(totalAlerts, null, 2));
    // console.log();

    // // Get most targeted locations for last 30 days
    // console.log('5. Most targeted locations (last 30 days):');
    // const monthAgo = new Date();
    // monthAgo.setDate(monthAgo.getDate() - 30);
    // const targetedLocations = await api.getMostTargetedLocations(monthAgo, api.getNow(), 5);
    // console.log(JSON.stringify(targetedLocations, null, 2));
    // console.log();

    // // Get real-time cached alerts
    // console.log('6. Real-time cached alerts:');
    // const cachedAlerts = await api.getRealTimeAlertCache();
    // console.log(JSON.stringify(cachedAlerts, null, 2));
    // console.log();

    // // Setup real-time connection (only if EventSource is available)
    // console.log('7. Testing real-time connection:');
    // const eventSource = api.createRealTimeConnection(
    //   (alerts) => {
    //     console.log('📢 New real-time alerts received:', alerts.length);
    //     alerts.forEach(alert => {
    //       console.log(`   - ${alert.name} (${alert.englishName}) at ${alert.timeStamp}`);
    //     });
    //   },
    //   (error) => {
    //     console.error('❌ Real-time connection error:', error.message);
    //   }
    // );

    // if (eventSource) {
    //   console.log('✅ Real-time connection established');
    //   // Close connection after 10 seconds
    //   setTimeout(() => {
    //     eventSource.close();
    //     console.log('🔌 Real-time connection closed');
    //   }, 10000);
    // }

  } catch (error) {
    console.error('❌ Example error:', error.message);
  }
}

// Export for use in other files
if (typeof module !== 'undefined' && module.exports) {
  module.exports = RocketAlertAPI;
}

// Make available globally in browser
if (typeof window !== 'undefined') {
  window.RocketAlertAPI = RocketAlertAPI;
}

// Auto-run examples when this file is executed directly
examples(); 