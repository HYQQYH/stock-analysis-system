"""Technical indicator calculation service using pandas-ta"""
import logging
from typing import Optional, Dict, Any

import pandas as pd
import pandas_ta as ta

logger = logging.getLogger(__name__)


class IndicatorCalculator:
    """Calculator for technical indicators using pandas-ta library."""

    def __init__(self):
        """Initialize the indicator calculator."""
        pass

    def calculate_macd(self, kline_df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
        """
        Calculate MACD (Moving Average Convergence Divergence) indicator.

        Args:
            kline_df: DataFrame with OHLCV data (must contain 'close' column)
            fast: Fast period for EMA (default: 12)
            slow: Slow period for EMA (default: 26)
            signal: Signal period for EMA (default: 9)

        Returns:
            DataFrame with original data plus MACD columns: MACD_12_26_9, MACDh_12_26_9, MACDs_12_26_9
        """
        if 'close' not in kline_df.columns:
            raise ValueError("DataFrame must contain 'close' column for MACD calculation")

        try:
            # Create a copy to avoid modifying the original DataFrame
            df = kline_df.copy()

            # Calculate MACD using pandas-ta
            macd = ta.macd(df['close'], fast=fast, slow=slow, signal=signal)

            # Merge MACD results with original DataFrame
            df = pd.concat([df, macd], axis=1)

            logger.info("MACD calculated successfully for %d rows", len(df))
            return df

        except Exception as e:
            logger.error("Error calculating MACD: %s", e)
            raise

    def calculate_kdj(self, kline_df: pd.DataFrame, length: int = 9, signal: int = 3) -> pd.DataFrame:
        """
        Calculate KDJ (Stochastic Oscillator) indicator.

        Args:
            kline_df: DataFrame with OHLCV data (must contain 'high', 'low', 'close' columns)
            length: Period for KDJ calculation (default: 9)
            signal: Signal period for smoothing (default: 3)

        Returns:
            DataFrame with original data plus KDJ columns: KDJ_K, KDJ_D, KDJ_J
        """
        if not all(col in kline_df.columns for col in ['high', 'low', 'close']):
            raise ValueError("DataFrame must contain 'high', 'low', 'close' columns for KDJ calculation")

        try:
            # Create a copy to avoid modifying the original DataFrame
            df = kline_df.copy()

            # Calculate Stochastic Oscillator using pandas-ta
            stoch = ta.stoch(
                high=df['high'],
                low=df['low'],
                close=df['close'],
                k=length,
                d=signal,
                smooth_k=signal
            )

            # Debug: Log columns returned by stoch function
            logger.info("Stochastic columns: %s", stoch.columns.tolist())

            # Get the actual column names from the result
            stoch_cols = stoch.columns.tolist()
            
            # Create KDJ columns with standard names
            if len(stoch_cols) >= 2:
                # Get the first two columns (K and D values)
                k_col = stoch_cols[0]
                d_col = stoch_cols[1]
                
                df['KDJ_K'] = stoch[k_col]
                df['KDJ_D'] = stoch[d_col]
                
                # Calculate J value: J = 3K - 2D
                df['KDJ_J'] = 3 * df['KDJ_K'] - 2 * df['KDJ_D']

            logger.info("KDJ calculated successfully for %d rows", len(df))
            return df

        except Exception as e:
            logger.error("Error calculating KDJ: %s", e)
            raise

    def calculate_rsi(self, kline_df: pd.DataFrame, length: int = 14) -> pd.DataFrame:
        """
        Calculate RSI (Relative Strength Index) indicator.

        Args:
            kline_df: DataFrame with OHLCV data (must contain 'close' column)
            length: Period for RSI calculation (default: 14)

        Returns:
            DataFrame with original data plus RSI column: RSI_14
        """
        if 'close' not in kline_df.columns:
            raise ValueError("DataFrame must contain 'close' column for RSI calculation")

        try:
            # Create a copy to avoid modifying the original DataFrame
            df = kline_df.copy()

            # Calculate RSI using pandas-ta
            rsi = ta.rsi(df['close'], length=length)

            # Rename column to match expected format
            rsi = rsi.rename(f'RSI_{length}')

            # Merge RSI results with original DataFrame
            df = pd.concat([df, rsi], axis=1)

            logger.info("RSI calculated successfully for %d rows", len(df))
            return df

        except Exception as e:
            logger.error("Error calculating RSI: %s", e)
            raise

    def calculate_all_indicators(
        self,
        kline_df: pd.DataFrame,
        macd_fast: int = 12,
        macd_slow: int = 26,
        macd_signal: int = 9,
        kdj_length: int = 9,
        kdj_signal: int = 3,
        rsi_length: int = 14
    ) -> pd.DataFrame:
        """
        Calculate all technical indicators at once.

        Args:
            kline_df: DataFrame with OHLCV data
            macd_fast: Fast period for MACD (default: 12)
            macd_slow: Slow period for MACD (default: 26)
            macd_signal: Signal period for MACD (default: 9)
            kdj_length: Period for KDJ (default: 9)
            kdj_signal: Signal period for KDJ (default: 3)
            rsi_length: Period for RSI (default: 14)

        Returns:
            DataFrame with original data plus all indicator columns
        """
        try:
            # Create a copy to avoid modifying the original DataFrame
            df = kline_df.copy()

            # Calculate MACD
            logger.info("Calculating MACD...")
            df = self.calculate_macd(df, fast=macd_fast, slow=macd_slow, signal=macd_signal)

            # Calculate KDJ
            logger.info("Calculating KDJ...")
            df = self.calculate_kdj(df, length=kdj_length, signal=kdj_signal)

            # Calculate RSI
            logger.info("Calculating RSI...")
            df = self.calculate_rsi(df, length=rsi_length)

            logger.info("All indicators calculated successfully for %d rows", len(df))
            return df

        except Exception as e:
            logger.error("Error calculating all indicators: %s", e)
            raise

    def validate_indicators(self, indicators_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Validate indicator values are within expected ranges.

        Args:
            indicators_df: DataFrame containing calculated indicators

        Returns:
            Dictionary with validation results
        """
        validation_results = {
            'valid': True,
            'issues': []
        }

        # Check RSI range (should be between 0 and 100)
        if 'RSI_14' in indicators_df.columns:
            rsi_values = indicators_df['RSI_14'].dropna()
            if len(rsi_values) > 0:
                rsi_valid = (rsi_values >= 0) & (rsi_values <= 100)
                if not rsi_valid.all():
                    invalid_count = (~rsi_valid).sum()
                    validation_results['valid'] = False
                    validation_results['issues'].append(
                        f"RSI has {invalid_count} values outside 0-100 range"
                    )

        # Check KDJ range (should be between 0 and 100, though J can go outside)
        if 'KDJ_K' in indicators_df.columns:
            k_values = indicators_df['KDJ_K'].dropna()
            if len(k_values) > 0:
                k_valid = (k_values >= 0) & (k_values <= 100)
                if not k_valid.all():
                    invalid_count = (~k_valid).sum()
                    validation_results['valid'] = False
                    validation_results['issues'].append(
                        f"KDJ_K has {invalid_count} values outside 0-100 range"
                    )

        if 'KDJ_D' in indicators_df.columns:
            d_values = indicators_df['KDJ_D'].dropna()
            if len(d_values) > 0:
                d_valid = (d_values >= 0) & (d_values <= 100)
                if not d_valid.all():
                    invalid_count = (~d_valid).sum()
                    validation_results['valid'] = False
                    validation_results['issues'].append(
                        f"KDJ_D has {invalid_count} values outside 0-100 range"
                    )

        # Check for excessive NaN values
        total_rows = len(indicators_df)
        for col in indicators_df.columns:
            if col.startswith(('MACD_', 'KDJ_', 'RSI_')):
                nan_count = indicators_df[col].isna().sum()
                nan_percentage = (nan_count / total_rows) * 100
                if nan_percentage > 50:  # Allow up to 50% NaN for warming periods
                    validation_results['valid'] = False
                    validation_results['issues'].append(
                        f"{col} has {nan_percentage:.1f}% NaN values"
                    )

        return validation_results
