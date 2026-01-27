"""Indicator management service for storage and retrieval"""
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

import pandas as pd
from sqlalchemy.orm import Session

from app.models.models import StockIndicators, KlineTypeEnum, StockInfo
from app.db.redis_cache import get_redis_client, cache_key_builder

logger = logging.getLogger(__name__)


class IndicatorManager:
    """Manager for storing, caching, and retrieving technical indicators"""

    # Cache TTL settings (in seconds)
    CACHE_TTL = {
        'indicators': 3600,  # 1 hour
        'daily': 86400,      # 1 day
        'weekly': 604800,    # 1 week
        'monthly': 2592000,  # 30 days
    }

    def __init__(self, db: Session = None):
        """Initialize indicator manager

        Args:
            db: SQLAlchemy database session (optional)
        """
        self.db = db
        self.redis = get_redis_client()

    def save_indicators(
        self,
        code: str,
        period: str,
        indicators_df: pd.DataFrame,
        db: Session = None
    ) -> bool:
        """
        Save indicator data to database.

        Args:
            code: Stock code
            period: K-line type (day/week/month)
            indicators_df: DataFrame containing indicator columns
            db: Database session (optional, uses instance db if not provided)

        Returns:
            True if successful, False otherwise
        """
        session = db or self.db
        if session is None:
            logger.error("Database session not provided")
            return False

        try:
            # Ensure stock exists in database
            stock = session.query(StockInfo).filter_by(stock_code=code).first()
            if not stock:
                logger.warning(f"Stock {code} not found, creating basic record")
                stock = StockInfo(
                    stock_code=code,
                    stock_name="Unknown",
                    exchange="SH" if code.startswith('6') else "SZ"
                )
                session.add(stock)
                session.flush()

            # Map period to enum
            period_enum = KlineTypeEnum(period)

            # Track saved records count
            saved_count = 0
            updated_count = 0

            # Iterate through DataFrame rows
            for idx, row in indicators_df.iterrows():
                trade_date = self._extract_date(row)

                # Prepare indicator data dictionary
                indicator_data = {}
                for col in indicators_df.columns:
                    if col.startswith(('MACD_', 'KDJ_', 'RSI_')):
                        value = row[col]
                        # Skip NaN values
                        if pd.notna(value):
                            indicator_data[col] = float(value)

                # Skip if no indicator data
                if not indicator_data:
                    continue

                # Check if record already exists
                existing = session.query(StockIndicators).filter_by(
                    stock_code=code,
                    indicator_type='all',
                    kline_type=period_enum,
                    trade_date=trade_date
                ).first()

                if existing:
                    # Update existing record
                    existing.indicator_data = indicator_data
                    existing.updated_at = datetime.utcnow()
                    updated_count += 1
                else:
                    # Create new record
                    indicator_record = StockIndicators(
                        stock_code=code,
                        indicator_type='all',
                        kline_type=period_enum,
                        trade_date=trade_date,
                        indicator_data=indicator_data
                    )
                    session.add(indicator_record)
                    saved_count += 1

            session.commit()
            logger.info(
                f"Saved {saved_count} new and updated {updated_count} indicator records "
                f"for {code} ({period})"
            )
            return True

        except Exception as e:
            session.rollback()
            logger.error(f"Error saving indicators for {code}: {e}")
            return False

    def cache_indicators(
        self,
        code: str,
        period: str,
        indicators_df: pd.DataFrame,
        ttl: int = None
    ) -> bool:
        """
        Cache indicator data to Redis.

        Args:
            code: Stock code
            period: K-line type (day/week/month)
            indicators_df: DataFrame containing indicator columns
            ttl: Cache TTL in seconds (optional, uses default if not provided)

        Returns:
            True if successful, False otherwise
        """
        try:
            # Build cache key
            cache_key = cache_key_builder('indicators', code, period)

            # Convert DataFrame to list of dictionaries for JSON serialization
            indicators_list = indicators_df.to_dict('records')

            # Convert datetime/date objects to strings for JSON serialization
            for record in indicators_list:
                for key, value in record.items():
                    if pd.notna(value) and hasattr(value, 'isoformat'):
                        record[key] = value.isoformat()

            # Get TTL based on period
            if ttl is None:
                ttl = self.CACHE_TTL.get(period, self.CACHE_TTL['indicators'])

            # Cache the data
            success = self.redis.set_json(cache_key, {
                'code': code,
                'period': period,
                'indicators': indicators_list,
                'cached_at': datetime.utcnow().isoformat()
            }, ttl=ttl)

            if success:
                logger.info(f"Cached indicators for {code} ({period}) with TTL {ttl}s")
            else:
                logger.warning(f"Failed to cache indicators for {code}")

            return success

        except Exception as e:
            logger.error(f"Error caching indicators for {code}: {e}")
            return False

    def get_indicators(
        self,
        code: str,
        period: str,
        from_cache: bool = True,
        db: Session = None
    ) -> Optional[pd.DataFrame]:
        """
        Retrieve indicator data for a stock.

        Args:
            code: Stock code
            period: K-line type (day/week/month)
            from_cache: Whether to try getting from cache first (default: True)
            db: Database session (optional)

        Returns:
            DataFrame with indicator data, or None if not found
        """
        session = db or self.db

        # Try to get from cache first
        if from_cache:
            cached_data = self._get_from_cache(code, period)
            if cached_data is not None:
                logger.info(f"Retrieved indicators for {code} from cache")
                return cached_data

        # Fall back to database
        if session is None:
            logger.error("Database session not provided and cache miss")
            return None

        try:
            # Map period to enum
            period_enum = KlineTypeEnum(period)

            # Query database for indicators
            query = session.query(StockIndicators).filter(
                StockIndicators.stock_code == code,
                StockIndicators.indicator_type == 'all',
                StockIndicators.kline_type == period_enum
            ).order_by(StockIndicators.trade_date)

            records = query.all()

            if not records:
                logger.warning(f"No indicators found for {code} ({period})")
                return None

            # Convert to list of dictionaries
            indicators_list = []
            for record in records:
                indicator_dict = {
                    'trade_date': record.trade_date,
                    **record.indicator_data
                }
                indicators_list.append(indicator_dict)

            # Convert to DataFrame
            df = pd.DataFrame(indicators_list)

            logger.info(f"Retrieved {len(df)} indicator records for {code} from database")
            return df

        except Exception as e:
            logger.error(f"Error retrieving indicators for {code}: {e}")
            return None

    def _get_from_cache(self, code: str, period: str) -> Optional[pd.DataFrame]:
        """
        Get indicator data from Redis cache.

        Args:
            code: Stock code
            period: K-line type

        Returns:
            DataFrame with indicator data, or None if not in cache
        """
        try:
            cache_key = cache_key_builder('indicators', code, period)
            cached_data = self.redis.get_json(cache_key)

            if cached_data:
                indicators_list = cached_data.get('indicators', [])
                if indicators_list:
                    df = pd.DataFrame(indicators_list)
                    # Convert trade_date back to datetime if needed
                    if 'trade_date' in df.columns:
                        df['trade_date'] = pd.to_datetime(df['trade_date'])
                    return df

            return None

        except Exception as e:
            logger.error(f"Error getting indicators from cache for {code}: {e}")
            return None

    def invalidate_cache(self, code: str, period: Optional[str] = None) -> int:
        """
        Invalidate cached indicator data.

        Args:
            code: Stock code
            period: K-line type (optional, if None clears all periods)

        Returns:
            Number of keys deleted
        """
        try:
            if period:
                cache_key = cache_key_builder('indicators', code, period)
                deleted = self.redis.delete(cache_key)
                logger.info(f"Invalidated cache for {code} ({period})")
            else:
                # Delete all periods for this stock
                pattern = cache_key_builder('indicators', code, '*')
                deleted = self.redis.delete_pattern(pattern)
                logger.info(f"Invalidated all cache keys for {code}")

            return deleted

        except Exception as e:
            logger.error(f"Error invalidating cache for {code}: {e}")
            return 0

    def _extract_date(self, row: pd.Series) -> datetime.date:
        """
        Extract trade date from DataFrame row.

        Args:
            row: DataFrame row

        Returns:
            Date object
        """
        # Try common date column names
        date_columns = ['date', 'trade_date', '日期']
        for col in date_columns:
            if col in row.index and pd.notna(row[col]):
                value = row[col]
                if isinstance(value, datetime):
                    return value.date()
                elif hasattr(value, 'to_pydatetime'):
                    return value.to_pydatetime().date()
                elif isinstance(value, str):
                    # Parse string date (adjust format as needed)
                    try:
                        return datetime.strptime(value, '%Y-%m-%d').date()
                    except ValueError:
                        pass

        # Fall back to index if it's a date/datetime
        if hasattr(row.name, 'date'):
            return row.name.date()
        elif isinstance(row.name, str):
            try:
                return datetime.strptime(row.name, '%Y-%m-%d').date()
            except ValueError:
                pass

        logger.warning(f"Could not extract date from row: {row}")
        return datetime.utcnow().date()

    def get_latest_indicators(
        self,
        code: str,
        period: str,
        n: int = 1,
        db: Session = None
    ) -> Optional[pd.DataFrame]:
        """
        Get the latest n indicator records.

        Args:
            code: Stock code
            period: K-line type
            n: Number of records to retrieve
            db: Database session (optional)

        Returns:
            DataFrame with latest n indicator records, or None if not found
        """
        df = self.get_indicators(code, period, db=db)
        if df is not None:
            return df.tail(n)
        return None

    def update_indicators(
        self,
        code: str,
        period: str,
        kline_df: pd.DataFrame,
        calculator,
        db: Session = None
    ) -> bool:
        """
        Calculate and update indicators for a stock.

        Args:
            code: Stock code
            period: K-line type
            kline_df: K-line data DataFrame
            calculator: IndicatorCalculator instance
            db: Database session (optional)

        Returns:
            True if successful, False otherwise
        """
        try:
            # Calculate indicators
            logger.info(f"Calculating indicators for {code} ({period})...")
            indicators_df = calculator.calculate_all_indicators(kline_df)

            # Validate indicators
            validation = calculator.validate_indicators(indicators_df)
            if not validation['valid']:
                logger.warning(f"Indicator validation failed for {code}: {validation['issues']}")
                # Continue anyway as some NaN values are expected during warmup

            # Save to database
            logger.info(f"Saving indicators to database for {code}...")
            save_success = self.save_indicators(code, period, indicators_df, db=db)

            if not save_success:
                logger.error(f"Failed to save indicators to database for {code}")
                return False

            # Cache to Redis
            logger.info(f"Caching indicators for {code}...")
            cache_success = self.cache_indicators(code, period, indicators_df)

            if not cache_success:
                logger.warning(f"Failed to cache indicators for {code}, but database save succeeded")
                return True  # Still consider successful as DB save worked

            logger.info(f"Successfully updated indicators for {code} ({period})")
            return True

        except Exception as e:
            logger.error(f"Error updating indicators for {code}: {e}")
            return False