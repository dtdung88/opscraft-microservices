

class AlertManager:
    """Advanced alerting with ML anomaly detection"""
    
    async def detect_anomalies(self, metrics: List[Metric]):
        """Use ML to detect anomalies in execution patterns"""
        from sklearn.ensemble import IsolationForest
        
        model = IsolationForest(contamination=0.1)
        predictions = model.fit_predict(metrics)
        
        anomalies = [m for m, p in zip(metrics, predictions) if p == -1]
        
        for anomaly in anomalies:
            await self.send_alert(anomaly)
    
    async def smart_alerting(self, event: Event):
        """Context-aware alerting with deduplication"""
        # Check if similar alert was sent recently
        if await self.is_duplicate_alert(event):
            return
        
        # Calculate severity based on context
        severity = await self.calculate_severity(event)
        
        # Route to appropriate channels
        await self.route_alert(event, severity)