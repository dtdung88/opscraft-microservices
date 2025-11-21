from sqlalchemy import Column, Integer, String, Text, JSON, ForeignKey, Enum as Boolean
from app.db.base import Base


class ScheduleDAG(Base):
    """Directed Acyclic Graph for schedule dependencies"""
    __tablename__ = "schedule_dags"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True)
    description = Column(Text)
    is_active = Column(Boolean, default=True)

class ScheduleNode(Base):
    """Node in schedule DAG"""
    __tablename__ = "schedule_nodes"
    
    id = Column(Integer, primary_key=True)
    dag_id = Column(Integer, ForeignKey("schedule_dags.id"))
    schedule_id = Column(Integer, ForeignKey("schedules.id"))
    node_order = Column(Integer)
    retry_policy = Column(JSON)

class ScheduleDependency(Base):
    """Dependency between schedule nodes"""
    __tablename__ = "schedule_dependencies"
    
    parent_node_id = Column(Integer, ForeignKey("schedule_nodes.id"))
    child_node_id = Column(Integer, ForeignKey("schedule_nodes.id"))
    dependency_type = Column(String(50))  # success, failure, always