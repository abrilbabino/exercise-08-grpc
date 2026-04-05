proto:
	python -m grpc_tools.protoc -I proto --python_out=. --grpc_python_out=. proto/node_registry.proto