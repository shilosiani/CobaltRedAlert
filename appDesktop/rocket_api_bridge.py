import subprocess
import json
import os
import logging
from typing import Dict, List, Optional, Any
from PyQt6.QtCore import QObject, pyqtSignal, QTimer, QProcess
import tempfile
import datetime

class RocketAPIBridge(QObject):
    """Bridge to use the JavaScript Rocket Alert API in Python"""
    
    # Signals
    new_alerts = pyqtSignal(list)
    api_error = pyqtSignal(str)
    connection_status_changed = pyqtSignal(bool)
    
    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
        self.node_process = None
        self.is_connected = False
        
        # Create temp directory for communication
        self.temp_dir = tempfile.mkdtemp(prefix="rocket_api_")
        self.results_file = os.path.join(self.temp_dir, "api_results.json")
        self.command_file = os.path.join(self.temp_dir, "api_command.json")
        
        # Timer for periodic checks
        self.check_timer = QTimer()
        self.check_timer.timeout.connect(self.check_for_alerts)
        
        self.setup_node_script()
    
    def setup_node_script(self):
        """Create Node.js script for API calls"""
        script_content = '''
const fs = require('fs');
const path = require('path');

// Import the RocketAlertAPI class
const RocketAlertAPI = require('./api_call/rocket_alert_api.js');

class APIBridge {
    constructor() {
        this.api = new RocketAlertAPI();
        this.tempDir = process.argv[2];
        this.resultsFile = path.join(this.tempDir, 'api_results.json');
        this.commandFile = path.join(this.tempDir, 'api_command.json');
        this.isRunning = true;
        
        console.log('🚀 Rocket Alert API Bridge started');
        this.startPolling();
    }
    
    async startPolling() {
        while (this.isRunning) {
            try {
                // Check for commands
                if (fs.existsSync(this.commandFile)) {
                    const command = JSON.parse(fs.readFileSync(this.commandFile, 'utf8'));
                    await this.executeCommand(command);
                    fs.unlinkSync(this.commandFile);
                }
                
                // Get real-time alerts
                const alerts = await this.api.getRealTimeAlertCache();
                
                // Get most recent alerts for comparison
                const recentAlerts = await this.api.getMostRecentAlerts(
                    this.api.get24HoursAgo(), 
                    this.api.getNow()
                );
                
                const result = {
                    timestamp: new Date().toISOString(),
                    realTimeAlerts: alerts,
                    recentAlerts: recentAlerts.slice(0, 10), // Last 10 alerts
                    status: 'success'
                };
                
                fs.writeFileSync(this.resultsFile, JSON.stringify(result, null, 2));
                
            } catch (error) {
                const errorResult = {
                    timestamp: new Date().toISOString(),
                    error: error.message,
                    status: 'error'
                };
                fs.writeFileSync(this.resultsFile, JSON.stringify(errorResult, null, 2));
                console.error('API Error:', error.message);
            }
            
            // Wait 3 seconds before next check
            await new Promise(resolve => setTimeout(resolve, 3000));
        }
    }
    
    async executeCommand(command) {
        try {
            let result;
            
            switch (command.action) {
                case 'getMostRecentAlert':
                    result = await this.api.getMostRecentAlert();
                    break;
                case 'getTotalAlerts':
                    result = await this.api.getTotalAlerts();
                    break;
                case 'getMostTargetedLocations':
                    result = await this.api.getMostTargetedLocations(null, null, command.limit || 10);
                    break;
                case 'getDailyStats':
                    result = await this.api.getTotalAlertsByDay();
                    break;
                default:
                    result = { error: 'Unknown command: ' + command.action };
            }
            
            const commandResult = {
                timestamp: new Date().toISOString(),
                command: command.action,
                result: result,
                status: 'success'
            };
            
            const commandResultFile = path.join(this.tempDir, `command_result_${Date.now()}.json`);
            fs.writeFileSync(commandResultFile, JSON.stringify(commandResult, null, 2));
            
        } catch (error) {
            console.error('Command execution error:', error);
        }
    }
}

// Start the bridge
new APIBridge();
'''
        
        self.node_script_file = os.path.join(self.temp_dir, "api_bridge.js")
        with open(self.node_script_file, 'w', encoding='utf-8') as f:
            f.write(script_content)
    
    def start_monitoring(self):
        """Start the Node.js API bridge"""
        try:
            # Change to the app directory where rocket_alert_api.js is located
            app_dir = os.path.dirname(os.path.abspath(__file__))
            
            # Start Node.js process
            self.node_process = QProcess(self)
            self.node_process.setWorkingDirectory(app_dir)
            self.node_process.finished.connect(self.on_process_finished)
            self.node_process.errorOccurred.connect(self.on_process_error)
            
            # Start the bridge script
            self.node_process.start("node", [self.node_script_file, self.temp_dir])
            
            if self.node_process.waitForStarted(5000):
                self.logger.info("🚀 Node.js API bridge started successfully")
                self.is_connected = True
                self.connection_status_changed.emit(True)
                
                # Start checking for results
                self.check_timer.start(2000)  # Check every 2 seconds
                return True
            else:
                self.logger.error("❌ Failed to start Node.js process")
                return False
                
        except Exception as e:
            self.logger.error(f"Error starting API bridge: {e}")
            self.api_error.emit(f"Failed to start API bridge: {str(e)}")
            return False
    
    def stop_monitoring(self):
        """Stop the API bridge"""
        self.check_timer.stop()
        
        if self.node_process and self.node_process.state() != QProcess.ProcessState.NotRunning:
            self.node_process.terminate()
            if not self.node_process.waitForFinished(3000):
                self.node_process.kill()
        
        self.is_connected = False
        self.connection_status_changed.emit(False)
        self.logger.info("🛑 API bridge stopped")
    
    def check_for_alerts(self):
        """Check for new alerts from the API"""
        try:
            if os.path.exists(self.results_file):
                with open(self.results_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if data.get('status') == 'success':
                    # Process real-time alerts
                    real_time_alerts = data.get('realTimeAlerts', {})
                    if real_time_alerts.get('alerts'):
                        self.process_alerts(real_time_alerts['alerts'])
                    
                    # Also check recent alerts for backup
                    recent_alerts = data.get('recentAlerts', [])
                    if recent_alerts:
                        # Only process if they're very recent (last 5 minutes)
                        import datetime
                        now = datetime.datetime.now()
                        for alert in recent_alerts[:3]:  # Check only the 3 most recent
                            # This would need proper timestamp parsing
                            pass
                
                elif data.get('status') == 'error':
                    error_msg = data.get('error', 'Unknown API error')
                    self.logger.warning(f"API Error: {error_msg}")
                    self.api_error.emit(error_msg)
        
        except Exception as e:
            self.logger.error(f"Error checking alerts: {e}")
    
    def process_alerts(self, alerts: List[Dict]):
        """Process incoming alerts and emit signal"""
        if not alerts:
            return
        
        processed_alerts = []
        for alert in alerts:
            processed_alert = {
                'id': alert.get('alertId', f"alert_{len(processed_alerts)}"),
                'title': 'התרעת צבע אדום',
                'cities': [alert.get('name', alert.get('englishName', 'Unknown'))],
                'description': f"התרעה באזור: {alert.get('name', alert.get('englishName', 'Unknown'))}",
                'timestamp': alert.get('timeStamp', ''),
                'alertType': alert.get('alertTypeId', 1),
                'duration': '90 seconds',  # Default duration
                'raw_data': alert
            }
            processed_alerts.append(processed_alert)
        
        if processed_alerts:
            self.logger.info(f"🚨 {len(processed_alerts)} new alerts detected")
            self.new_alerts.emit(processed_alerts)
    
    def execute_command(self, action: str, **kwargs):
        """Execute a command in the Node.js bridge"""
        try:
            command = {
                'action': action,
                'timestamp': datetime.datetime.now().isoformat(),
                **kwargs
            }
            
            with open(self.command_file, 'w', encoding='utf-8') as f:
                json.dump(command, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"📤 Command sent: {action}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error executing command {action}: {e}")
            return False
    
    def get_most_recent_alert(self):
        """Get the most recent alert"""
        return self.execute_command('getMostRecentAlert')
    
    def get_total_alerts(self):
        """Get total alerts count"""
        return self.execute_command('getTotalAlerts')
    
    def get_most_targeted_locations(self, limit: int = 10):
        """Get most targeted locations"""
        return self.execute_command('getMostTargetedLocations', limit=limit)
    
    def get_daily_stats(self):
        """Get daily statistics"""
        return self.execute_command('getDailyStats')
    
    def on_process_finished(self, exit_code):
        """Handle process finished"""
        self.is_connected = False
        self.connection_status_changed.emit(False)
        self.logger.warning(f"Node.js process finished with code: {exit_code}")
        
        if exit_code != 0:
            self.api_error.emit(f"API process crashed with code: {exit_code}")
    
    def on_process_error(self, error):
        """Handle process errors"""
        self.is_connected = False
        self.connection_status_changed.emit(False)
        error_msg = f"Node.js process error: {error}"
        self.logger.error(error_msg)
        self.api_error.emit(error_msg)
    
    def cleanup(self):
        """Clean up resources"""
        self.stop_monitoring()
        
        # Clean up temp files
        try:
            import shutil
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        except Exception as e:
            self.logger.warning(f"Error cleaning up temp directory: {e}") 