#!/usr/bin/env python3
"""
Advanced Trading Agents with Competitive Intelligence
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import asyncio
import time
from scipy.fft import fft, fftfreq
from scipy.signal import welch, find_peaks
from sklearn.ensemble import IsolationForest
from sklearn.cluster import DBSCAN
from sklearn.decomposition import PCA
import networkx as nx
from multi_agent_system import TradingAgent, TradingSignal
import logging

class MarketMicrostructureAgent(TradingAgent):
    """Analyzes order book patterns and market microstructure"""

    def __init__(self):
        super().__init__("MICROSTRUCTURE_001", "market_microstructure")
        self.order_flow_history = []
        self.spread_patterns = {}
        self.volume_profile = {}

    async def generate_signal(self, symbol: str, market_data: Dict) -> Optional[TradingSignal]:
        try:
            price = market_data.get('price', 0)
            volume = market_data.get('volume', 0)
            spread = market_data.get('spread', 0.01)

            # Analyze order flow imbalance
            order_flow_signal = await self.analyze_order_flow(symbol, price, volume)

            # Detect hidden liquidity patterns
            liquidity_signal = await self.detect_liquidity_patterns(symbol, spread, volume)

            # Market impact analysis
            impact_signal = await self.analyze_market_impact(symbol, price, volume)

            # Combine signals
            combined_confidence = (order_flow_signal + liquidity_signal + impact_signal) / 3

            if combined_confidence > 0.7:
                return TradingSignal(
                    agent_id=self.agent_id,
                    symbol=symbol,
                    action='buy' if order_flow_signal > 0 else 'sell',
                    confidence=combined_confidence,
                    strategy='microstructure',
                    price=price,
                    timestamp=datetime.now(),
                    reasoning=f"Microstructure edge: OF={order_flow_signal:.3f}, LIQ={liquidity_signal:.3f}, IMP={impact_signal:.3f}",
                    risk_score=0.3,
                    expected_return=combined_confidence * 0.003,
                    timeframe='scalp'
                )

        except Exception as e:
            self.logger.error(f"Microstructure agent error: {e}")

        return None

    async def analyze_order_flow(self, symbol: str, price: float, volume: float) -> float:
        """Analyze order flow imbalance"""
        # Simulate order flow analysis
        # In reality, this would analyze Level 2 order book data

        if symbol not in self.order_flow_history:
            self.order_flow_history = []

        self.order_flow_history.append({
            'price': price,
            'volume': volume,
            'timestamp': time.time()
        })

        if len(self.order_flow_history) > 50:
            self.order_flow_history.pop(0)

        if len(self.order_flow_history) >= 10:
            recent_volumes = [entry['volume'] for entry in self.order_flow_history[-10:]]
            recent_prices = [entry['price'] for entry in self.order_flow_history[-10:]]

            # Calculate volume-weighted pressure
            price_changes = np.diff(recent_prices)
            volume_weights = recent_volumes[1:]

            if len(price_changes) > 0 and np.sum(volume_weights) > 0:
                vwap_momentum = np.sum(price_changes * volume_weights) / np.sum(volume_weights)
                return np.tanh(vwap_momentum * 1000)  # Normalize to [-1, 1]

        return 0.0

    async def detect_liquidity_patterns(self, symbol: str, spread: float, volume: float) -> float:
        """Detect hidden liquidity and spread patterns"""
        # Track spread-volume relationship
        if symbol not in self.spread_patterns:
            self.spread_patterns[symbol] = []

        self.spread_patterns[symbol].append({
            'spread': spread,
            'volume': volume,
            'timestamp': time.time()
        })

        if len(self.spread_patterns[symbol]) > 20:
            self.spread_patterns[symbol].pop(0)

        if len(self.spread_patterns[symbol]) >= 10:
            spreads = [p['spread'] for p in self.spread_patterns[symbol]]
            volumes = [p['volume'] for p in self.spread_patterns[symbol]]

            # Detect abnormal spread-volume relationships
            avg_spread = np.mean(spreads)
            avg_volume = np.mean(volumes)

            # Low spread + high volume = good liquidity
            if spread < avg_spread * 0.8 and volume > avg_volume * 1.2:
                return 0.8  # Strong positive signal

            # High spread + low volume = poor liquidity
            elif spread > avg_spread * 1.2 and volume < avg_volume * 0.8:
                return -0.8  # Strong negative signal

        return 0.0

    async def analyze_market_impact(self, symbol: str, price: float, volume: float) -> float:
        """Analyze price impact of volume"""
        # Simplified market impact model
        # Price impact typically follows square root of volume

        if volume > 0:
            # Estimate impact based on volume
            normalized_volume = volume / 1000000  # Normalize to millions
            estimated_impact = np.sqrt(normalized_volume) * 0.001

            # Return inverse signal (low impact = good for trading)
            return np.tanh(1 / (1 + estimated_impact))

        return 0.0

class FrequencyDomainAgent(TradingAgent):
    """Uses FFT and spectral analysis for pattern detection"""

    def __init__(self):
        super().__init__("FREQUENCY_001", "spectral_analysis")
        self.price_series = {}
        self.dominant_frequencies = {}

    async def generate_signal(self, symbol: str, market_data: Dict) -> Optional[TradingSignal]:
        try:
            price = market_data.get('price', 0)

            # Build price series
            if symbol not in self.price_series:
                self.price_series[symbol] = []

            self.price_series[symbol].append(price)

            # Keep only recent data for analysis
            if len(self.price_series[symbol]) > 256:
                self.price_series[symbol] = self.price_series[symbol][-256:]

            if len(self.price_series[symbol]) >= 64:  # Minimum for FFT
                # Perform spectral analysis
                signal_strength = await self.analyze_frequency_domain(symbol)

                if signal_strength != 0:
                    action = 'buy' if signal_strength > 0 else 'sell'
                    confidence = min(0.9, abs(signal_strength))

                    return TradingSignal(
                        agent_id=self.agent_id,
                        symbol=symbol,
                        action=action,
                        confidence=confidence,
                        strategy='spectral',
                        price=price,
                        timestamp=datetime.now(),
                        reasoning=f"Spectral pattern detected: strength={signal_strength:.3f}",
                        risk_score=0.4,
                        expected_return=confidence * 0.004,
                        timeframe='short'
                    )

        except Exception as e:
            self.logger.error(f"Frequency domain agent error: {e}")

        return None

    async def analyze_frequency_domain(self, symbol: str) -> float:
        """Analyze price series in frequency domain"""
        try:
            prices = np.array(self.price_series[symbol])

            # Remove trend
            detrended = prices - np.mean(prices)

            # Apply FFT
            fft_values = fft(detrended)
            frequencies = fftfreq(len(detrended))

            # Find dominant frequencies
            power_spectrum = np.abs(fft_values) ** 2
            dominant_freq_idx = np.argmax(power_spectrum[1:len(power_spectrum)//2]) + 1

            # Analyze phase and amplitude
            dominant_freq = frequencies[dominant_freq_idx]
            dominant_amplitude = np.abs(fft_values[dominant_freq_idx])
            dominant_phase = np.angle(fft_values[dominant_freq_idx])

            # Generate signal based on phase prediction
            # Predict next price movement based on dominant cycle
            if dominant_amplitude > np.std(power_spectrum):
                # Strong periodic component detected
                phase_prediction = dominant_phase + 2 * np.pi * dominant_freq

                # Convert phase to signal
                signal_strength = np.sin(phase_prediction) * (dominant_amplitude / np.max(power_spectrum))
                return np.tanh(signal_strength * 10)  # Normalize

        except Exception as e:
            self.logger.warning(f"FFT analysis failed: {e}")

        return 0.0

class AnomalyDetectionAgent(TradingAgent):
    """Detects market anomalies and unusual patterns"""

    def __init__(self):
        super().__init__("ANOMALY_001", "anomaly_detection")
        self.isolation_forest = IsolationForest(contamination=0.1, random_state=42)
        self.feature_history = []
        self.is_trained = False

    async def generate_signal(self, symbol: str, market_data: Dict) -> Optional[TradingSignal]:
        try:
            # Extract features for anomaly detection
            features = await self.extract_anomaly_features(market_data)

            if features is not None:
                self.feature_history.append(features)

                # Keep sliding window
                if len(self.feature_history) > 200:
                    self.feature_history.pop(0)

                # Train model when enough data
                if not self.is_trained and len(self.feature_history) >= 50:
                    await self.train_anomaly_detector()

                # Detect anomalies
                if self.is_trained:
                    anomaly_score = await self.detect_anomaly(features)

                    if abs(anomaly_score) > 0.7:  # Strong anomaly
                        action = 'buy' if anomaly_score < 0 else 'sell'  # Contrarian
                        confidence = min(0.95, abs(anomaly_score))

                        return TradingSignal(
                            agent_id=self.agent_id,
                            symbol=symbol,
                            action=action,
                            confidence=confidence,
                            strategy='anomaly',
                            price=market_data.get('price', 0),
                            timestamp=datetime.now(),
                            reasoning=f"Market anomaly detected: score={anomaly_score:.3f}",
                            risk_score=0.6,
                            expected_return=confidence * 0.006,
                            timeframe='short'
                        )

        except Exception as e:
            self.logger.error(f"Anomaly detection agent error: {e}")

        return None

    async def extract_anomaly_features(self, market_data: Dict) -> Optional[List[float]]:
        """Extract features for anomaly detection"""
        try:
            price = market_data.get('price', 0)
            volume = market_data.get('volume', 0)
            spread = market_data.get('spread', 0.01)
            timestamp = market_data.get('timestamp', time.time())

            # Time-based features
            hour = datetime.fromtimestamp(timestamp).hour
            minute = datetime.fromtimestamp(timestamp).minute

            # Price-based features
            price_norm = price / 50000  # Normalize BTC price roughly

            # Volume-based features
            volume_norm = volume / 1000000  # Normalize volume

            # Spread features
            spread_norm = spread / 0.01  # Normalize spread

            features = [
                price_norm,
                volume_norm,
                spread_norm,
                hour / 24,
                minute / 60,
                np.sin(2 * np.pi * hour / 24),  # Cyclical hour
                np.cos(2 * np.pi * hour / 24),
            ]

            return features

        except Exception:
            return None

    async def train_anomaly_detector(self):
        """Train the anomaly detection model"""
        try:
            if len(self.feature_history) >= 50:
                X = np.array(self.feature_history)
                self.isolation_forest.fit(X)
                self.is_trained = True
                self.logger.info("Anomaly detector trained")
        except Exception as e:
            self.logger.error(f"Anomaly detector training failed: {e}")

    async def detect_anomaly(self, features: List[float]) -> float:
        """Detect if current features are anomalous"""
        try:
            if self.is_trained:
                X = np.array([features])
                anomaly_score = self.isolation_forest.decision_function(X)[0]
                return anomaly_score
        except Exception:
            pass

        return 0.0

class CompetitiveIntelligenceAgent(TradingAgent):
    """Analyzes trading patterns to detect other algorithms"""

    def __init__(self):
        super().__init__("COMPETITIVE_001", "competitive_intelligence")
        self.trade_patterns = {}
        self.algo_signatures = {}
        self.market_participants = {}

    async def generate_signal(self, symbol: str, market_data: Dict) -> Optional[TradingSignal]:
        try:
            # Analyze trading patterns to identify algorithmic behavior
            algo_activity = await self.detect_algorithmic_activity(symbol, market_data)

            # Identify front-running opportunities
            front_run_signal = await self.detect_front_running_opportunity(symbol, market_data)

            # Detect latency arbitrage opportunities
            latency_signal = await self.detect_latency_opportunity(symbol, market_data)

            # Combine competitive intelligence signals
            competitive_edge = (algo_activity + front_run_signal + latency_signal) / 3

            if abs(competitive_edge) > 0.6:
                action = 'buy' if competitive_edge > 0 else 'sell'
                confidence = min(0.9, abs(competitive_edge))

                return TradingSignal(
                    agent_id=self.agent_id,
                    symbol=symbol,
                    action=action,
                    confidence=confidence,
                    strategy='competitive_intel',
                    price=market_data.get('price', 0),
                    timestamp=datetime.now(),
                    reasoning=f"Competitive edge detected: algo_activity={algo_activity:.3f}, front_run={front_run_signal:.3f}, latency={latency_signal:.3f}",
                    risk_score=0.5,
                    expected_return=confidence * 0.005,
                    timeframe='scalp'
                )

        except Exception as e:
            self.logger.error(f"Competitive intelligence agent error: {e}")

        return None

    async def detect_algorithmic_activity(self, symbol: str, market_data: Dict) -> float:
        """Detect patterns indicating algorithmic trading"""
        # Track order patterns
        timestamp = market_data.get('timestamp', time.time())
        price = market_data.get('price', 0)
        volume = market_data.get('volume', 0)

        if symbol not in self.trade_patterns:
            self.trade_patterns[symbol] = []

        self.trade_patterns[symbol].append({
            'timestamp': timestamp,
            'price': price,
            'volume': volume
        })

        # Keep recent data
        if len(self.trade_patterns[symbol]) > 100:
            self.trade_patterns[symbol] = self.trade_patterns[symbol][-100:]

        if len(self.trade_patterns[symbol]) >= 20:
            # Analyze for algorithmic patterns
            recent_trades = self.trade_patterns[symbol][-20:]

            # Check for regular timing patterns (HFT signature)
            intervals = []
            for i in range(1, len(recent_trades)):
                interval = recent_trades[i]['timestamp'] - recent_trades[i-1]['timestamp']
                intervals.append(interval)

            # High frequency + regular intervals = algorithmic
            if intervals:
                avg_interval = np.mean(intervals)
                interval_std = np.std(intervals)

                # Very regular timing suggests algorithmic activity
                if avg_interval < 1.0 and interval_std < 0.1:  # Sub-second regular intervals
                    return 0.8  # High algo activity

                # Check for volume clustering (another algo signature)
                volumes = [t['volume'] for t in recent_trades]
                volume_clusters = len(set(np.round(volumes, -3)))  # Round to nearest 1000

                if volume_clusters < 5:  # Few distinct volume levels
                    return 0.6  # Medium algo activity

        return 0.0

    async def detect_front_running_opportunity(self, symbol: str, market_data: Dict) -> float:
        """Detect opportunities to front-run slower algorithms"""
        # Look for large pending orders or predictable algo patterns
        # This is a simplified implementation

        price = market_data.get('price', 0)
        volume = market_data.get('volume', 0)

        # Detect large volume spikes that might indicate pending large orders
        if symbol in self.trade_patterns and len(self.trade_patterns[symbol]) >= 10:
            recent_volumes = [t['volume'] for t in self.trade_patterns[symbol][-10:]]
            avg_volume = np.mean(recent_volumes)

            # Current volume significantly higher than average
            if volume > avg_volume * 2:
                # Potential large order - opportunity to front-run
                return 0.7

        return 0.0

    async def detect_latency_opportunity(self, symbol: str, market_data: Dict) -> float:
        """Detect latency arbitrage opportunities"""
        # Look for price discrepancies that can be exploited with speed
        # This would typically involve cross-venue arbitrage

        # Simplified: detect rapid price movements that others might be slow to react to
        if symbol in self.trade_patterns and len(self.trade_patterns[symbol]) >= 5:
            recent_prices = [t['price'] for t in self.trade_patterns[symbol][-5:]]

            # Rapid price movement in last few ticks
            if len(recent_prices) >= 2:
                price_change = (recent_prices[-1] - recent_prices[0]) / recent_prices[0]

                # Significant price movement = potential latency opportunity
                if abs(price_change) > 0.001:  # 0.1% movement
                    return np.tanh(abs(price_change) * 1000)

        return 0.0

class NetworkEffectAgent(TradingAgent):
    """Analyzes network effects and social sentiment"""

    def __init__(self):
        super().__init__("NETWORK_001", "network_effects")
        self.sentiment_history = {}
        self.network_graph = nx.Graph()
        self.influence_scores = {}

    async def generate_signal(self, symbol: str, market_data: Dict) -> Optional[TradingSignal]:
        try:
            # Simulate network analysis
            network_signal = await self.analyze_network_effects(symbol, market_data)

            # Simulate sentiment analysis
            sentiment_signal = await self.analyze_market_sentiment(symbol)

            # Social momentum detection
            social_momentum = await self.detect_social_momentum(symbol)

            # Combine network signals
            combined_signal = (network_signal + sentiment_signal + social_momentum) / 3

            if abs(combined_signal) > 0.6:
                action = 'buy' if combined_signal > 0 else 'sell'
                confidence = min(0.85, abs(combined_signal))

                return TradingSignal(
                    agent_id=self.agent_id,
                    symbol=symbol,
                    action=action,
                    confidence=confidence,
                    strategy='network_effects',
                    price=market_data.get('price', 0),
                    timestamp=datetime.now(),
                    reasoning=f"Network effects: net={network_signal:.3f}, sent={sentiment_signal:.3f}, social={social_momentum:.3f}",
                    risk_score=0.4,
                    expected_return=confidence * 0.008,
                    timeframe='medium'
                )

        except Exception as e:
            self.logger.error(f"Network effect agent error: {e}")

        return None

    async def analyze_network_effects(self, symbol: str, market_data: Dict) -> float:
        """Analyze network propagation effects"""
        # Simulate network analysis
        # In practice, this would analyze social media, news, etc.

        current_time = time.time()
        hour = datetime.fromtimestamp(current_time).hour

        # Simulate network activity patterns
        # Higher activity during certain hours
        if 9 <= hour <= 16:  # Business hours
            base_activity = 0.3
        elif 20 <= hour <= 23:  # Evening
            base_activity = 0.2
        else:
            base_activity = 0.1

        # Add some randomness
        noise = np.random.normal(0, 0.1)
        network_activity = base_activity + noise

        return np.tanh(network_activity * 2)

    async def analyze_market_sentiment(self, symbol: str) -> float:
        """Analyze market sentiment indicators"""
        # Simulate sentiment analysis
        # This would integrate with news feeds, social media, etc.

        # Generate synthetic sentiment based on price action
        if symbol in self.sentiment_history:
            # Simple momentum-based sentiment
            return np.random.normal(0, 0.3)  # Random sentiment for simulation

        return 0.0

    async def detect_social_momentum(self, symbol: str) -> float:
        """Detect social trading momentum"""
        # Simulate social momentum detection
        # This would analyze retail trading patterns, social media trends, etc.

        # Generate synthetic social momentum
        momentum = np.random.normal(0, 0.2)
        return np.tanh(momentum)