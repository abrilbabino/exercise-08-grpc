from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import grpc
import node_registry_pb2
import node_registry_pb2_grpc
from google.protobuf.json_format import MessageToDict

app = FastAPI()

channel = grpc.insecure_channel('grpc-server:50051')
stub = node_registry_pb2_grpc.NodeRegistryStub(channel)

class NodeCreate(BaseModel):
    name: str
    host: str
    port: int

@app.post("/api/nodes", status_code=201)
def register_node(node: NodeCreate):
    try:
        request = node_registry_pb2.RegisterRequest(name=node.name, host=node.host, port=node.port)
        response = stub.Register(request)
        return MessageToDict(response, preserving_proto_field_name=True)
    except grpc.RpcError as e:
        if e.code() == grpc.StatusCode.ALREADY_EXISTS:
            raise HTTPException(status_code=409, detail=e.details())
        raise HTTPException(status_code=500, detail="Internal error")

@app.get("/api/nodes")
def list_nodes():
    response = stub.List(node_registry_pb2.Empty())
    return MessageToDict(response, preserving_proto_field_name=True).get("nodes", [])

@app.get("/api/nodes/{name}")
def get_node(name: str):
    try:
        response = stub.Get(node_registry_pb2.GetRequest(name=name))
        return MessageToDict(response, preserving_proto_field_name=True)
    except grpc.RpcError as e:
        if e.code() == grpc.StatusCode.NOT_FOUND:
            raise HTTPException(status_code=404, detail=e.details())
        raise HTTPException(status_code=500, detail="Internal error")

@app.delete("/api/nodes/{name}", status_code=204)
def delete_node(name: str):
    try:
        stub.Delete(node_registry_pb2.DeleteRequest(name=name))
        return
    except grpc.RpcError as e:
        if e.code() == grpc.StatusCode.NOT_FOUND:
            raise HTTPException(status_code=404, detail=e.details())
        raise HTTPException(status_code=500, detail="Internal error")

@app.get("/health")
def health():
    return {"status": "ok"}