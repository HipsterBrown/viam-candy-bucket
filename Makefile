buf-generate:
	buf generate --template ./src/proto/buf.gen.yaml ./src/proto -o ./src/proto

bundle:
	tar -czf module.tar.gz *.sh .env src requirements.txt

upload:
	viam module upload --version $(version) --platform linux/arm64 module.tar.gz

clean:
	rm module.tar.gz

build: buf-generate

publish: bundle upload clean
