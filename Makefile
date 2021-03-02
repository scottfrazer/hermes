clean:
	-rm sapling hermes_parser.go
bootstrap:
	hermes generate -l go hermes.new.zgr
compile:
	go fmt *.go
	go build -o sapling
test: clean bootstrap compile
	go test -v
