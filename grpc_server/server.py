import grpc
from concurrent import futures
import logging
import os
from datetime import datetime, timezone
import node_registry_pb2
import node_registry_pb2_grpc
import time

from sqlalchemy.exc import OperationalError
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://noderegistry:noderegistry@db:5432/noderegistry")
engine = None
for attempt in range(15):
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect():
            pass
        logging.info("Connected to database")
        break
    except OperationalError:
        logging.info(f"DB not ready (attempt {attempt + 1}/15), retrying in 3s...")
        time.sleep(3)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Node(Base):
    __tablename__ = "nodes"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    host = Column(String, nullable=False)
    port = Column(Integer, nullable=False)
    status = Column(String, default="active")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

Base.metadata.create_all(bind=engine)

class NodeRegistryServicer(node_registry_pb2_grpc.NodeRegistryServicer):
    def Register(self, request, context):
        db = SessionLocal()
        existing = db.query(Node).filter(Node.name == request.name).first()
        if existing:
            context.set_code(grpc.StatusCode.ALREADY_EXISTS)
            context.set_details('Node already exists')
            db.close()
            return node_registry_pb2.NodeResponse()
        
        new_node = Node(name=request.name, host=request.host, port=request.port)
        db.add(new_node)
        db.commit()
        db.refresh(new_node)
        
        response = node_registry_pb2.NodeResponse(
            id=new_node.id, name=new_node.name, host=new_node.host,
            port=new_node.port, status=new_node.status,
            created_at=str(new_node.created_at), updated_at=str(new_node.updated_at)
        )
        db.close()
        return response

    def List(self, request, context):
        db = SessionLocal()
        nodes = db.query(Node).all()
        response_nodes = [
            node_registry_pb2.NodeResponse(
                id=n.id, name=n.name, host=n.host, port=n.port,
                status=n.status, created_at=str(n.created_at), updated_at=str(n.updated_at)
            ) for n in nodes
        ]
        db.close()
        return node_registry_pb2.NodeList(nodes=response_nodes)

    def Get(self, request, context):
        db = SessionLocal()
        node = db.query(Node).filter(Node.name == request.name).first()
        db.close()
        if not node:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details('Node not found')
            return node_registry_pb2.NodeResponse()
        
        return node_registry_pb2.NodeResponse(
            id=node.id, name=node.name, host=node.host, port=node.port,
            status=node.status, created_at=str(node.created_at), updated_at=str(node.updated_at)
        )

    def Delete(self, request, context):
        db = SessionLocal()
        node = db.query(Node).filter(Node.name == request.name).first()
        if not node:
            db.close()
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details('Node not found')
            return node_registry_pb2.Empty()
        
        node.status = "inactive"
        node.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.close()
        return node_registry_pb2.Empty()

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    node_registry_pb2_grpc.add_NodeRegistryServicer_to_server(NodeRegistryServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    logging.info("gRPC Server running on port 50051...")
    server.wait_for_termination()

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    serve()