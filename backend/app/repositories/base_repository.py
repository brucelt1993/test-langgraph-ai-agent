"""
Base repository interface and implementation.
"""

from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Optional, List, Dict, Any, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update, func, and_, or_, desc, asc
from sqlalchemy.orm import selectinload, joinedload
from uuid import uuid4
import logging

from app.core.database import Base

logger = logging.getLogger(__name__)

# Type variables for generic repository
T = TypeVar('T', bound=Base)
ID = TypeVar('ID', str, int)


class PaginationResult(Generic[T]):
    """Pagination result container."""
    
    def __init__(
        self, 
        items: List[T], 
        total: int, 
        page: int, 
        page_size: int,
        total_pages: int
    ):
        self.items = items
        self.total = total
        self.page = page
        self.page_size = page_size
        self.total_pages = total_pages
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "items": self.items,
            "pagination": {
                "total": self.total,
                "page": self.page,
                "page_size": self.page_size,
                "total_pages": self.total_pages,
                "has_next": self.page < self.total_pages,
                "has_prev": self.page > 1
            }
        }


class BaseRepository(Generic[T], ABC):
    """Base repository with common CRUD operations."""
    
    def __init__(self, session: AsyncSession, model_class: type[T]):
        self.session = session
        self.model_class = model_class
        
    async def create(self, **kwargs) -> T:
        """Create a new record."""
        try:
            # Add UUID if not provided
            if hasattr(self.model_class, 'id') and 'id' not in kwargs:
                kwargs['id'] = str(uuid4())
                
            instance = self.model_class(**kwargs)
            self.session.add(instance)
            await self.session.flush()
            await self.session.refresh(instance)
            
            logger.debug(f"Created {self.model_class.__name__} with id: {instance.id}")
            return instance
            
        except Exception as e:
            logger.error(f"Error creating {self.model_class.__name__}: {e}")
            await self.session.rollback()
            raise
    
    async def get_by_id(self, id: ID, load_relations: bool = False) -> Optional[T]:
        """Get record by ID."""
        try:
            query = select(self.model_class).where(self.model_class.id == id)
            
            if load_relations and hasattr(self.model_class, '__relationships__'):
                for rel in self.model_class.__relationships__:
                    query = query.options(selectinload(getattr(self.model_class, rel)))
            
            result = await self.session.execute(query)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Error getting {self.model_class.__name__} by id {id}: {e}")
            raise
    
    async def get_all(
        self, 
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: Optional[str] = None,
        order_direction: str = "asc",
        filters: Optional[Dict[str, Any]] = None
    ) -> List[T]:
        """Get all records with optional filtering and ordering."""
        try:
            query = select(self.model_class)
            
            # Apply filters
            if filters:
                for key, value in filters.items():
                    if hasattr(self.model_class, key):
                        column = getattr(self.model_class, key)
                        if isinstance(value, list):
                            query = query.where(column.in_(value))
                        elif isinstance(value, dict):
                            # Support for range queries, etc.
                            for op, val in value.items():
                                if op == "gte":
                                    query = query.where(column >= val)
                                elif op == "lte":
                                    query = query.where(column <= val)
                                elif op == "gt":
                                    query = query.where(column > val)
                                elif op == "lt":
                                    query = query.where(column < val)
                                elif op == "like":
                                    query = query.where(column.like(f"%{val}%"))
                        else:
                            query = query.where(column == value)
            
            # Apply ordering
            if order_by and hasattr(self.model_class, order_by):
                column = getattr(self.model_class, order_by)
                if order_direction.lower() == "desc":
                    query = query.order_by(desc(column))
                else:
                    query = query.order_by(asc(column))
            
            # Apply pagination
            if offset:
                query = query.offset(offset)
            if limit:
                query = query.limit(limit)
            
            result = await self.session.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error getting all {self.model_class.__name__}: {e}")
            raise
    
    async def get_paginated(
        self,
        page: int = 1,
        page_size: int = 20,
        order_by: Optional[str] = None,
        order_direction: str = "asc",
        filters: Optional[Dict[str, Any]] = None
    ) -> PaginationResult[T]:
        """Get paginated records."""
        try:
            # Calculate offset
            offset = (page - 1) * page_size
            
            # Get total count
            count_query = select(func.count()).select_from(self.model_class)
            if filters:
                for key, value in filters.items():
                    if hasattr(self.model_class, key):
                        column = getattr(self.model_class, key)
                        if isinstance(value, list):
                            count_query = count_query.where(column.in_(value))
                        else:
                            count_query = count_query.where(column == value)
            
            total_result = await self.session.execute(count_query)
            total = total_result.scalar()
            
            # Get records
            items = await self.get_all(
                limit=page_size,
                offset=offset,
                order_by=order_by,
                order_direction=order_direction,
                filters=filters
            )
            
            # Calculate total pages
            total_pages = (total + page_size - 1) // page_size
            
            return PaginationResult(
                items=items,
                total=total,
                page=page,
                page_size=page_size,
                total_pages=total_pages
            )
            
        except Exception as e:
            logger.error(f"Error getting paginated {self.model_class.__name__}: {e}")
            raise
    
    async def update(self, id: ID, **kwargs) -> Optional[T]:
        """Update record by ID."""
        try:
            # Remove None values
            kwargs = {k: v for k, v in kwargs.items() if v is not None}
            
            if not kwargs:
                return await self.get_by_id(id)
            
            query = (
                update(self.model_class)
                .where(self.model_class.id == id)
                .values(**kwargs)
                .returning(self.model_class.id)
            )
            
            result = await self.session.execute(query)
            updated_id = result.scalar_one_or_none()
            
            if updated_id:
                await self.session.commit()
                return await self.get_by_id(updated_id)
            
            return None
            
        except Exception as e:
            logger.error(f"Error updating {self.model_class.__name__} with id {id}: {e}")
            await self.session.rollback()
            raise
    
    async def delete(self, id: ID, soft_delete: bool = True) -> bool:
        """Delete record by ID."""
        try:
            if soft_delete and hasattr(self.model_class, 'deleted_at'):
                # Soft delete
                from datetime import datetime, timezone
                result = await self.update(id, deleted_at=datetime.now(timezone.utc))
                return result is not None
            else:
                # Hard delete
                query = delete(self.model_class).where(self.model_class.id == id)
                result = await self.session.execute(query)
                await self.session.commit()
                return result.rowcount > 0
                
        except Exception as e:
            logger.error(f"Error deleting {self.model_class.__name__} with id {id}: {e}")
            await self.session.rollback()
            raise
    
    async def exists(self, **kwargs) -> bool:
        """Check if record exists with given conditions."""
        try:
            query = select(func.count()).select_from(self.model_class)
            
            for key, value in kwargs.items():
                if hasattr(self.model_class, key):
                    column = getattr(self.model_class, key)
                    query = query.where(column == value)
            
            result = await self.session.execute(query)
            return result.scalar() > 0
            
        except Exception as e:
            logger.error(f"Error checking existence in {self.model_class.__name__}: {e}")
            raise
    
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count records with optional filters."""
        try:
            query = select(func.count()).select_from(self.model_class)
            
            if filters:
                for key, value in filters.items():
                    if hasattr(self.model_class, key):
                        column = getattr(self.model_class, key)
                        query = query.where(column == value)
            
            result = await self.session.execute(query)
            return result.scalar()
            
        except Exception as e:
            logger.error(f"Error counting {self.model_class.__name__}: {e}")
            raise