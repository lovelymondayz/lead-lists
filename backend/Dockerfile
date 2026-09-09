FROM golang:1.22-alpine AS builder

WORKDIR /app
COPY go.mod ./
RUN go mod download

COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -o server ./cmd/server

FROM alpine:3.19
RUN apk add --no-cache ca-certificates curl && adduser -D -u 1000 leadlists
WORKDIR /app
COPY --from=builder /app/server .

RUN mkdir -p /app/data /app/output && chown -R leadlists:leadlists /app

USER leadlists

ENV PORT=8000
EXPOSE 8000

CMD ["./server"]
