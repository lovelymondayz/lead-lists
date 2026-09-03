FROM golang:1.22-alpine AS builder

WORKDIR /app
COPY go.mod ./
RUN go mod download

COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -o server ./cmd/server

FROM alpine:3.19
RUN apk add --no-cache ca-certificates curl
WORKDIR /app
COPY --from=builder /app/server .

RUN mkdir -p /app/data /app/output
ENV PORT=8000
EXPOSE 8000
CMD ["./server"]

# Run as non-root
USER 1000:1000
